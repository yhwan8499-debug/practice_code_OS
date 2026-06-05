#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <sys/shm.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

#define SHM_NAME "/my_shm"
#define SHM_SIZE 4096

// 공유 메모리에서 데이터를 읽어오는 프로그램
int main(void)
{
    // 공유 메모리 객체 생성
    int fd = shm_open(SHM_NAME, O_RDONLY, S_IRUSR | S_IWUSR);
    if (fd == -1) {             // 공유 메모리 객체 열기 실패, 에러처리
        perror("shm_open");
        exit(EXIT_FAILURE);
    }

    // 메모리 파일을 실제 주소에 연결
    char *addr = mmap(NULL, SHM_SIZE, PROT_READ, MAP_SHARED, fd, 0);
    if (addr == MAP_FAILED) {
        perror("mmap");
        exit(EXIT_FAILURE);
    }

    printf("Read from shared memory: %s\n", addr);

    munmap(addr, SHM_SIZE);
    close(fd);

    shm_unlink(SHM_NAME);
    return 0;
}