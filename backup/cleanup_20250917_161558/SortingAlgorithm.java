package com.example.sorting;

import java.util.Arrays;
import java.util.Random;

/**
 * 多种排序算法实现
 * 包含冒泡排序、选择排序、插入排序、快速排序、归并排序等
 */
public class SortingAlgorithm {
    
    /**
     * 冒泡排序
     * 时间复杂度：O(n²)
     * 空间复杂度：O(1)
     */
    public static void bubbleSort(int[] arr) {
        if (arr == null || arr.length <= 1) {
            return;
        }
        
        int n = arr.length;
        for (int i = 0; i < n - 1; i++) {
            boolean swapped = false;
            for (int j = 0; j < n - i - 1; j++) {
                if (arr[j] > arr[j + 1]) {
                    // 交换元素
                    swap(arr, j, j + 1);
                    swapped = true;
                }
            }
            // 如果没有发生交换，说明数组已经有序
            if (!swapped) {
                break;
            }
        }
    }
    
    /**
     * 选择排序
     * 时间复杂度：O(n²)
     * 空间复杂度：O(1)
     */
    public static void selectionSort(int[] arr) {
        if (arr == null || arr.length <= 1) {
            return;
        }
        
        int n = arr.length;
        for (int i = 0; i < n - 1; i++) {
            int minIndex = i;
            // 找到最小元素的索引
            for (int j = i + 1; j < n; j++) {
                if (arr[j] < arr[minIndex]) {
                    minIndex = j;
                }
            }
            // 交换元素
            if (minIndex != i) {
                swap(arr, i, minIndex);
            }
        }
    }
    
    /**
     * 插入排序
     * 时间复杂度：O(n²)
     * 空间复杂度：O(1)
     */
    public static void insertionSort(int[] arr) {
        if (arr == null || arr.length <= 1) {
            return;
        }
        
        for (int i = 1; i < arr.length; i++) {
            int key = arr[i];
            int j = i - 1;
            
            // 将大于key的元素向后移动
            while (j >= 0 && arr[j] > key) {
                arr[j + 1] = arr[j];
                j--;
            }
            arr[j + 1] = key;
        }
    }
    
    /**
     * 快速排序
     * 时间复杂度：平均O(n log n)，最坏O(n²)
     * 空间复杂度：O(log n)
     */
    public static void quickSort(int[] arr) {
        if (arr == null || arr.length <= 1) {
            return;
        }
        quickSort(arr, 0, arr.length - 1);
    }
    
    private static void quickSort(int[] arr, int low, int high) {
        if (low < high) {
            // 分区操作
            int pivotIndex = partition(arr, low, high);
            
            // 递归排序左半部分
            quickSort(arr, low, pivotIndex - 1);
            // 递归排序右半部分
            quickSort(arr, pivotIndex + 1, high);
        }
    }
    
    private static int partition(int[] arr, int low, int high) {
        // 选择最后一个元素作为基准
        int pivot = arr[high];
        int i = low - 1; // 小于基准的元素的索引
        
        for (int j = low; j < high; j++) {
            if (arr[j] <= pivot) {
                i++;
                swap(arr, i, j);
            }
        }
        
        // 将基准元素放到正确位置
        swap(arr, i + 1, high);
        return i + 1;
    }
    
    /**
     * 归并排序
     * 时间复杂度：O(n log n)
     * 空间复杂度：O(n)
     */
    public static void mergeSort(int[] arr) {
        if (arr == null || arr.length <= 1) {
            return;
        }
        mergeSort(arr, 0, arr.length - 1);
    }
    
    private static void mergeSort(int[] arr, int left, int right) {
        if (left < right) {
            int mid = left + (right - left) / 2;
            
            // 递归排序左半部分
            mergeSort(arr, left, mid);
            // 递归排序右半部分
            mergeSort(arr, mid + 1, right);
            
            // 合并两个有序数组
            merge(arr, left, mid, right);
        }
    }
    
    private static void merge(int[] arr, int left, int mid, int right) {
        // 创建临时数组
        int[] temp = new int[right - left + 1];
        
        int i = left;    // 左半部分的起始索引
        int j = mid + 1; // 右半部分的起始索引
        int k = 0;       // 临时数组的索引
        
        // 合并两个有序数组
        while (i <= mid && j <= right) {
            if (arr[i] <= arr[j]) {
                temp[k++] = arr[i++];
            } else {
                temp[k++] = arr[j++];
            }
        }
        
        // 复制剩余元素
        while (i <= mid) {
            temp[k++] = arr[i++];
        }
        while (j <= right) {
            temp[k++] = arr[j++];
        }
        
        // 将临时数组的元素复制回原数组
        for (i = 0; i < temp.length; i++) {
            arr[left + i] = temp[i];
        }
    }
    
    /**
     * 堆排序
     * 时间复杂度：O(n log n)
     * 空间复杂度：O(1)
     */
    public static void heapSort(int[] arr) {
        if (arr == null || arr.length <= 1) {
            return;
        }
        
        int n = arr.length;
        
        // 构建最大堆
        for (int i = n / 2 - 1; i >= 0; i--) {
            heapify(arr, n, i);
        }
        
        // 逐个提取元素
        for (int i = n - 1; i > 0; i--) {
            // 将根节点（最大值）与最后一个元素交换
            swap(arr, 0, i);
            
            // 重新调整堆
            heapify(arr, i, 0);
        }
    }
    
    private static void heapify(int[] arr, int n, int i) {
        int largest = i;    // 假设根节点最大
        int left = 2 * i + 1;  // 左子节点
        int right = 2 * i + 2; // 右子节点
        
        // 如果左子节点比根节点大
        if (left < n && arr[left] > arr[largest]) {
            largest = left;
        }
        
        // 如果右子节点比当前最大值大
        if (right < n && arr[right] > arr[largest]) {
            largest = right;
        }
        
        // 如果最大值不是根节点
        if (largest != i) {
            swap(arr, i, largest);
            
            // 递归调整受影响的子树
            heapify(arr, n, largest);
        }
    }
    
    /**
     * 交换数组中两个元素的位置
     */
    private static void swap(int[] arr, int i, int j) {
        int temp = arr[i];
        arr[i] = arr[j];
        arr[j] = temp;
    }
    
    /**
     * 生成随机数组
     */
    public static int[] generateRandomArray(int size, int maxValue) {
        Random random = new Random();
        int[] arr = new int[size];
        for (int i = 0; i < size; i++) {
            arr[i] = random.nextInt(maxValue);
        }
        return arr;
    }
    
    /**
     * 复制数组
     */
    public static int[] copyArray(int[] arr) {
        return Arrays.copyOf(arr, arr.length);
    }
    
    /**
     * 验证数组是否已排序
     */
    public static boolean isSorted(int[] arr) {
        for (int i = 1; i < arr.length; i++) {
            if (arr[i] < arr[i - 1]) {
                return false;
            }
        }
        return true;
    }
    
    /**
     * 打印数组
     */
    public static void printArray(int[] arr) {
        System.out.println(Arrays.toString(arr));
    }
    
    /**
     * 测试所有排序算法
     */
    public static void main(String[] args) {
        // 测试数据
        int[] testArray = generateRandomArray(20, 100);
        System.out.println("原始数组：");
        printArray(testArray);
        System.out.println();
        
        // 测试各种排序算法
        testSortingAlgorithm("冒泡排序", testArray, SortingAlgorithm::bubbleSort);
        testSortingAlgorithm("选择排序", testArray, SortingAlgorithm::selectionSort);
        testSortingAlgorithm("插入排序", testArray, SortingAlgorithm::insertionSort);
        testSortingAlgorithm("快速排序", testArray, SortingAlgorithm::quickSort);
        testSortingAlgorithm("归并排序", testArray, SortingAlgorithm::mergeSort);
        testSortingAlgorithm("堆排序", testArray, SortingAlgorithm::heapSort);
    }
    
    /**
     * 测试排序算法
     */
    private static void testSortingAlgorithm(String algorithmName, int[] originalArray, 
                                           java.util.function.Consumer<int[]> sortingFunction) {
        int[] testArray = copyArray(originalArray);
        
        long startTime = System.nanoTime();
        sortingFunction.accept(testArray);
        long endTime = System.nanoTime();
        
        long duration = (endTime - startTime) / 1000; // 转换为微秒
        
        System.out.println(algorithmName + "：");
        System.out.println("  排序结果：" + (isSorted(testArray) ? "正确" : "错误"));
        System.out.println("  执行时间：" + duration + " 微秒");
        printArray(testArray);
        System.out.println();
    }
}
