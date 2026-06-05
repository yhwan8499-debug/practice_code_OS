#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/shm.h>
#include <sys/mman.h>
#include <sys/stat.h>

#define SHM_NAME "/my_shm"
#define SHM_SIZE 4096
#define MESSAGE "Hello world from writer!"

// 공유 메모리에 데이터를 쓰는 프로그램
int main(void)
{

    // 공유 메모리 객체 생성
    int fd = shm_open(SHM_NAME, O_CREAT | O_RDWR, S_IRUSR | S_IWUSR);
    if (fd == -1) {
        perror("shm_open");
        exit(EXIT_FAILURE);
    }

    // 공유 메모리 파일의 크기를 설정
    if (ftruncate(fd, SHM_SIZE) == -1) {
        perror("ftruncate");
        exit(EXIT_FAILURE);
    }

    // 메모리 파일을 실제 주소에 연결
    char *addr = mmap(NULL, SHM_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (addr == MAP_FAILED) {
        perror("mmap");
        exit(EXIT_FAILURE);
    }

    // 메시지를 공유 메모리 영역에 복사
    const char message[] = MESSAGE;
    memcpy(addr, message, strlen(message));

    printf("Written to shared memory: %s\n", message);

    munmap(addr, SHM_SIZE);
    close(fd);

    return 0;
}