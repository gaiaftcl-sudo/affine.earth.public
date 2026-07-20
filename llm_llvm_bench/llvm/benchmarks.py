from typing import List
from ..core.types import LLVMTestSample

MICROBENCH_C: LLVMTestSample = LLVMTestSample(
    sample_id="llvm_micro_matrix_mul",
    domain="microbench",
    language="c",
    source_code="""
#include <stdio.h>
#include <stdlib.h>

#define N 200

void matmul(double A[N][N], double B[N][N], double C[N][N]) {
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            C[i][j] = 0.0;
            for (int k = 0; k < N; k++) {
                C[i][j] += A[i][k] * B[k][j];
            }
        }
    }
}

int main() {
    static double A[N][N], B[N][N], C[N][N];
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            A[i][j] = (double)(i + j);
            B[i][j] = (double)(i - j);
        }
    }
    matmul(A, B, C);
    printf("C[0][0] = %f\\n", C[0][0]);
    return 0;
}
""",
)

CODESIZE_C: LLVMTestSample = LLVMTestSample(
    sample_id="llvm_codesize_sort",
    domain="codesize",
    language="c",
    source_code="""
#include <stdio.h>

void bubble_sort(int arr[], int n) {
    for (int i = 0; i < n - 1; i++) {
        for (int j = 0; j < n - i - 1; j++) {
            if (arr[j] > arr[j + 1]) {
                int temp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = temp;
            }
        }
    }
}

int main() {
    int arr[] = {64, 34, 25, 12, 22, 11, 90};
    int n = sizeof(arr) / sizeof(arr[0]);
    bubble_sort(arr, n);
    return 0;
}
""",
)

LIST_OF_LLVM_BENCHMARKS = [MICROBENCH_C, CODESIZE_C]

def get_llvm_benchmark(benchmark_id: str) -> LLVMTestSample:
    for b in LIST_OF_LLVM_BENCHMARKS:
        if b.sample_id == benchmark_id:
            return b
    return MICROBENCH_C
