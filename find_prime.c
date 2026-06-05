#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <pthread.h>
#include <semaphore.h>
#include <stdbool.h>
#include <time.h>

#define NUM_THREADS 128        // 64개의 일꾼, 과제할 때 숫자를 바꿔서 실험하기
#define MAX_NUMBER 10000000  // 0~1000만까지 소수, 이것도
#define CHUNK_SIZE 10000000       // 1000씩 끊어서 소수 찾기, 마지막에 전역변수에 저장, 이것도

uint32_t current_number = 2;    // current_number: 지금까지 소수를 찾았는가?
uint32_t total_primes = 0;      // 최종적으로 발견한 소수의 개수
sem_t sem_task, sem_result;     // sem_task: 일꾼들이 작업할 숫자 범위를 얻기 위해 사용하는 세마포어
                                // sem_result: 일꾼들이 발견한 소수의 개수를 업데이트하기 위해 사용하는 세마포어

bool is_prime(uint32_t n) {
    if (n <= 1) return false;
    if (n <= 3) return true;
    if (n % 2 == 0 || n % 3 == 0) return false;
    
    for (uint64_t i = 5; i * i <= n; i = i + 6) {
        if (n % i == 0 || n % (i + 2) == 0) return false; 
    }
    return true;
}

void* find_primes(void* arg) {
    uint32_t thread_id = *(uint32_t*)arg;
    uint32_t local_primes = 0;          // 지속적인 전역 변수 접근을 막기 위한 지역 변수

    while (true) {
        // 어디서부터 어디까지 작업
        uint32_t start_num, end_num;

        // current_number 변수 업데이트
        // current_number 변수 보호
        sem_wait(&sem_task);
        start_num = current_number;
        current_number += CHUNK_SIZE;
        sem_post(&sem_task);

        if (start_num > MAX_NUMBER) {
            break;
        }

        end_num = start_num + CHUNK_SIZE - 1;
        if (end_num > MAX_NUMBER) {
            end_num = MAX_NUMBER;
        }

        for (uint32_t i = start_num; i <= end_num; i++) {
            if (is_prime(i)) {
                // printf("Thread %d found prime: %d\n", thread_id, i);
                local_primes++;
            }
        }
    }

    // 현재 chunk에서 찾은 소수 개수를 전체 소수 개수에 더하기
    // 전역 변수 보호
    sem_wait(&sem_result);
    total_primes += local_primes;
    sem_post(&sem_result);

    return NULL;
}

int main() {
    pthread_t threads[NUM_THREADS];
    uint32_t thread_ids[NUM_THREADS];
    struct timespec start, end;             // 시간 측정을 위한 변수

    // sem_task: current_number를 보호하기 위한 세마포어
    // sem_result: total_primes를 보호하기 위한 세마포어
    if (sem_init(&sem_task, 0, 1) != 0) {
        perror("Semaphore initialization failed");
        exit(EXIT_FAILURE);
    }
    if (sem_init(&sem_result, 0, 1) != 0) {
        perror("Semaphore initialization failed");
        exit(EXIT_FAILURE);
    }

    // 시작 시간 측정
    clock_gettime(CLOCK_MONOTONIC, &start);

    // MAX_THREADS의 개수 만큼 일꾼 스레드 생성
    for (size_t i = 0; i < NUM_THREADS; i++) {
        thread_ids[i] = i + 1;
        if (pthread_create(&threads[i], NULL, find_primes, &thread_ids[i]) != 0) {
            perror("Thread creation failed");
            exit(EXIT_FAILURE);
        }
    }

    // 작업 중인 스레드 기다리기
    for (size_t i = 0; i < NUM_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }

    // 종료 시점 시간 측정
    clock_gettime(CLOCK_MONOTONIC, &end);
    time_t seconds = end.tv_sec - start.tv_sec;
    long nanoseconds = end.tv_nsec - start.tv_nsec;
    double elapsed_time = (double)seconds + (double)nanoseconds * 1.0E-9;

    printf("Total prime numbers found up to %u: %u\n", MAX_NUMBER, total_primes);
    printf("elapsed time: %.9lf s\n", elapsed_time);

    sem_destroy(&sem_task);
    sem_destroy(&sem_result);

    return 0;
}
