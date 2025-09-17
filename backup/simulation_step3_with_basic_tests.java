public class SortingAlgorithm {
    
    /**
     * 快速排序算法
     */
    public static void quickSort(int[] arr, int low, int high) {
        if (low < high) {
            int pi = partition(arr, low, high);
            quickSort(arr, low, pi - 1);
            quickSort(arr, pi + 1, high);
        }
    }
    
    private static int partition(int[] arr, int low, int high) {
        int pivot = arr[high];
        int i = (low - 1);
        
        for (int j = low; j < high; j++) {
            if (arr[j] <= pivot) {
                i++;
                int temp = arr[i];
                arr[i] = arr[j];
                arr[j] = temp;
            }
        }
        
        int temp = arr[i + 1];
        arr[i + 1] = arr[high];
        arr[high] = temp;
        
        return i + 1;
    }
    
    private static void printArray(int[] arr) {
        for (int value : arr) {
            System.out.print(value + " ");
        }
        System.out.println();
    }
    
    public static void main(String[] args) {
        // 基本测试用例
        int[] arr1 = {64, 34, 25, 12, 22, 11, 90};
        System.out.println("原数组:");
        printArray(arr1);
        
        quickSort(arr1, 0, arr1.length - 1);
        System.out.println("排序后:");
        printArray(arr1);
        
        // 边界测试
        int[] arr2 = {5};
        quickSort(arr2, 0, arr2.length - 1);
        System.out.println("单元素数组排序:");
        printArray(arr2);
    }
}
