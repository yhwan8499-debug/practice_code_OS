#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <semaphore.h>

#define ITER 100000

volatile int c = 0;
sem_t s1, s2;

void *thread1(void *arg) {
    for (int i = 0; i < ITER; i++) {
        sem_wait(&s1);
        //printf("t1\n");
        c++;
        sem_post(&s2);
    }
}

void *thread2(void *arg) {
    for (int i = 0; i < ITER; i++) {
        sem_wait(&s2);
        //printf("t2\n");
        c++;
        sem_post(&s1);
    }
}

int main(void)
{
    // 세마포 초기화 하나는 1로, 하나는 0으로 초기화
    if (sem_init(&s1, 0, 1)) {
        perror("Semaphore initialization failed");
        exit(EXIT_FAILURE);
    }
    if (sem_init(&s2, 0, 0)) {
        perror("Semaphore initialization failed");
        exit(EXIT_FAILURE);
    }

    // 스레드 식별자
    pthread_t t1, t2;

    // 스레드 생성
    // 1: 스레드 식별자의 주소
    // 2: 스레드 속성 (기본값 NULL)
    // 3: 스레드가 싱행할 함수 포인터
    // 4: 매개변수
    if (pthread_create(&t1, NULL, thread1, NULL)) {
        perror("Thread creation failed");
        exit(EXIT_FAILURE);
    }
    if (pthread_create(&t2, NULL, thread2, NULL)) {
        perror("Thread creation failed");
        exit(EXIT_FAILURE);
    }

    // 스레드 1과 스레드 2가 끝날때 까지 기다림
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    
    printf("c = %d\n", c);

    sem_destroy(&s1);
    sem_destroy(&s2);
    return 0;
}
