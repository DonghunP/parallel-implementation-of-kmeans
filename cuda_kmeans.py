import csv, time, random, math, sys
import pycuda.driver as cuda
import pycuda.autoinit
from pycuda.compiler import SourceModule
import numpy
import pycuda.driver as drv

def eucl_distance(point_one, point_two):
	if(len(point_one) != len(point_two)):
		raise Exception("Error: non comparable points")

	sum_diff = 0.0
	for i in range(len(point_one)):
		diff = pow((float(point_one[i]) - float(point_two[i])), 2) # L2 Norm
		sum_diff += diff
	final = math.sqrt(sum_diff)
	return final


def main():	
	global cutoff, dimensions, dataset, num_clusters, data
	print("Enter the number of clusters you want to make:")
	num_clusters = input()
	num_clusters = int(num_clusters)

	with open('modified_video_game_sales.csv', 'rt') as f:
		reader = csv.reader(f)
		dataset = list(reader)

	initial = []
	dataset.pop(0) # delete first row
	data = dataset

	for i in range(num_clusters): # 10
		initial.append(dataset[i]) # Why add dataset[1], dataset[2], dataset[3] to initial list?
	#	dataset.pop(0)

	f = open("cluster.txt", 'w+')
	f.write(str(initial))

	initial = numpy.array(initial)
	initial = initial.astype(numpy.float32)

	num_points = []
	dimensions = []

	num_points.append(num_clusters)
	num_points = numpy.array(num_points)
	num_points = num_points.astype(numpy.int32)

	dimensions.append(len(data[0])) #9
	dimensions = numpy.array(dimensions)
	dimensions = dimensions.astype(numpy.int32)
	
	cutoff = 0.2
	loop = 0
	clusters = []
	points = []

	for i in range(len(data)): #make blank list as number of data column
		points.append([0])
	
	data = numpy.array(data)
	data = data.astype(numpy.float32)
	
	points = numpy.array(points)
	points = points.astype(numpy.int32)
	
	points_gpu = cuda.mem_alloc(points.size * points.dtype.itemsize)
	cuda.memcpy_htod(points_gpu, points)

	data_gpu = cuda.mem_alloc(data.size * data.dtype.itemsize)
	cuda.memcpy_htod(data_gpu, data)

	initial_gpu = cuda.mem_alloc( initial.size * initial.dtype.itemsize) # 10????
	l = cuda.mem_alloc(dimensions.dtype.itemsize) # 10
	cuda.memcpy_htod(l, dimensions)

	noc = cuda.mem_alloc(num_points.dtype.itemsize)
	cuda.memcpy_htod(noc, num_points)	# 10

	compare_cutoff = True	
	start_time = time.time()

	while compare_cutoff:
		cuda.memcpy_htod(initial_gpu, initial) # initial_gpu, data_gpu, points_gpu, l, noc
		mod = SourceModule("""	
	    	__global__ void kmeans(float * a, float *c, int * d, int * len, int * noc)
	    	{
	      		int idx = blockIdx.x;
			int li;
			float least = 99999999;
			
			for(int i = 0; i< noc[0]; i++){
				float sum = 0.0;	
						
				for(int j = 0; j< len[0]; j++){
					sum += ((a[i*len[0] + j] - c[idx*len[0] +j])* (a[i*len[0] + j] - c[idx*len[0] +j]));
				}
		
				if( sum < least){
					least  = sum;
					li = i;		
				}
			}	
			d[idx] = li; 			
	    	}
	    	""")

		func = mod.get_function("kmeans")	
		func(initial_gpu, data_gpu, points_gpu, l, noc, block=(1, 1, 1), grid=(len(data), 1, 1))	
		pc = numpy.empty_like(points)
		cuda.memcpy_dtoh(pc, points_gpu)
		no = []
		tot = []

		for i in range(len(initial)):
			no.append(0)
			tot.append([])
			for j in range(len(initial[0])):
				tot[-1].append(0)
		for i in range(len(pc)):
			no[int(pc[i])] += 1                   # fixed
			for j in range(len(initial[0])):
				tot[int(pc[i])][j] += data[i][j]  # fixed
		
		for i in range(len(tot)):
			if(no[i] != 0):
				for j in range(len(initial[0])):
					tot[i][j] /= no[i]
		flag = 0		
		for i in range(len(tot)):
			if eucl_distance(tot[i], initial[i]) > cutoff:
				flag += 1
		if flag == 0:
			compare_cutoff = False
			print(tot)
			f.write(str(tot))
		else:
			tot = numpy.array(tot)
			initial = tot.astype(numpy.float32)
	print("Execution time %s seconds" % (time.time() - start_time))
	f.close()
if __name__ == "__main__":
	start_time = time.time()
	main()
	
