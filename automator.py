import os
import re
import subprocess
import matplotlib.pyplot as plt
import numpy as np

# ==========================================
# 🧪 1. 실험 매크로 설정 구역
# ==========================================
THREADS_LIST = [1, 2, 4, 8, 12, 16, 32, 64, 128]        # X축 스펙
CHUNK_LIST = [1, 10, 100, 1000, 10000, 100000, 1000000, 5000000, 10000000] # Y축 스펙
MAX_NUMBER = 100000000                       # 탐색 상한선 (이 값에 따라 폴더가 생성됩니다)
LOOP_COUNT = 3                              # 오차 제거를 위한 반복 측정 횟수

C_FILE_NAME = "find_prime.c"
TARGET_EXE = "./prime_test"

def modify_c_file(threads, max_num, chunk):
    """C 소스코드의 #define 매크로 값을 자동으로 수정"""
    with open(C_FILE_NAME, "r", encoding="utf-8") as f:
        code = f.read()
    code = re.sub(r"#define\s+NUM_THREADS\s+\d+", f"#define NUM_THREADS {threads}", code)
    code = re.sub(r"#define\s+MAX_NUMBER\s+\d+", f"#define MAX_NUMBER {max_num}", code)
    code = re.sub(r"#define\s+CHUNK_SIZE\s+\d+", f"#define CHUNK_SIZE {chunk}", code)
    with open(C_FILE_NAME, "w", encoding="utf-8") as f:
        f.write(code)

def compile_c_file():
    """gcc 컴파일 진행"""
    compile_cmd = ["gcc", "-O2", "-pthread", C_FILE_NAME, "-o", TARGET_EXE]
    result = subprocess.run(compile_cmd, capture_output=True, text=True)
    return result.returncode == 0

def run_benchmark():
    """프로그램 실행 후 소요 시간 추출"""
    result = subprocess.run([TARGET_EXE], capture_output=True, text=True)
    if result.returncode != 0:
        return None
    match = re.search(r"elapsed time:\s*([\d.]+)\s*s", result.stdout)
    return float(match.group(1)) if match else None

def main():
    total_cases = len(CHUNK_LIST) * len(THREADS_LIST)
    current_case = 0

    print("🚀 [완전 자동화 매크로] 벤치마크 및 폴더별 4대 그래프 생성을 시작합니다...")
    print(f"📍 총 실험 세트 수: {total_cases}개 (각 세트당 {LOOP_COUNT}회 반복 수행)")
    
    # 결과 저장용 폴더 자동 생성 구역 (ex: result_50000000)
    output_dir = f"result_{MAX_NUMBER}"
    os.makedirs(output_dir, exist_ok=True)
    
    # 격자 구조 데이터 매트릭스 준비 (행: 청크 크기, 열: 스레드 개수)
    grid_times = np.zeros((len(CHUNK_LIST), len(THREADS_LIST)))

    # 81가지 경우의 수 순회 실행
    for c_idx, chunk in enumerate(CHUNK_LIST):
        for t_idx, thread in enumerate(THREADS_LIST):
            current_case += 1
            
            print(f"\n⚙️ [{current_case}/{total_cases}] 세트 설정 중 ➡️ THREADS: {thread}개, CHUNK: {chunk}")
            
            modify_c_file(thread, MAX_NUMBER, chunk)
            if not compile_c_file():
                print("❌ 컴파일 에러로 인해 스크립트를 중단합니다.")
                return

            captured_times = []
            for i in range(LOOP_COUNT):
                print(f"  [{current_case}/{total_cases}] ({i+1}/{LOOP_COUNT} 회차) 측정 중... ", end="", flush=True)
                elapsed = run_benchmark()
                
                if elapsed is not None:
                    print(f"{elapsed:.4f} 초")
                    captured_times.append(elapsed)
                else:
                    print("실패")

            if captured_times:
                avg_time = sum(captured_times) / len(captured_times)
                print(f" 🌟 [{current_case}/{total_cases}] 평균 소요 시간: {avg_time:.4f} 초")
                grid_times[c_idx, t_idx] = avg_time

    # --------------------------------------------------------
    # 1. 보고서용 마크다운 표 출력 구역 ★ (부활 및 완벽 동기화)
    # --------------------------------------------------------
    print("\n" + "="*60)
    print("📊 보고서에 그대로 복사해서 넣을 마크다운 표 결과")
    print("="*60)
    print("| CHUNK_SIZE | NUM_THREADS | 평균 수행 시간 (Elapsed Time) |")
    print("| :--- | :--- | :--- |")
    for c_idx, chunk in enumerate(CHUNK_LIST):
        for t_idx, thread in enumerate(THREADS_LIST):
            print(f"| {chunk} | {thread}개 | {grid_times[c_idx, t_idx]:.4f} s |")
    print("="*60)

    # 시각화용 Grid Mesh 생성
    X_mesh, Y_mesh = np.meshgrid(THREADS_LIST, CHUNK_LIST)

    # --------------------------------------------------------
    # 2. Figure 1 : 3D Surface (지정 폴더 저장 적용)
    # --------------------------------------------------------
    print("\n🎨 [Figure 1] 3D Surface 생성 중...")
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')

    # 로그 변환
    Y_mesh_log = np.log10(Y_mesh)

    surf = ax.plot_surface(
        X_mesh, Y_mesh_log, grid_times,
        cmap='viridis', edgecolor='k', linewidth=0.3, alpha=0.85
    )

    ax.scatter(X_mesh, Y_mesh_log, grid_times, color='red', s=30)

    ax.set_title(f"Execution Time Surface (MAX={MAX_NUMBER:,})", fontsize=14)
    ax.set_xlabel("Threads")
    ax.set_ylabel("Chunk Size")
    ax.set_zlabel("Time (s)")

    tick_chunks = [1, 10, 100, 1000, 10000, 100000, 1000000, 10000000]
    ax.set_yticks([np.log10(x) for x in tick_chunks])
    ax.set_yticklabels([str(x) for x in tick_chunks])

    ax.view_init(elev=30, azim=-45)
    fig.colorbar(surf, shrink=0.6, aspect=12)
    
    # 각 파일 저장 경로를 os.path.join을 통해 새로 만든 폴더 내부로 고정 ★
    plt.savefig(os.path.join(output_dir, "Figure1_3D_Surface.png"), dpi=300, bbox_inches='tight')
    plt.close()

    # --------------------------------------------------------
    # 3. Figure 2 : Execution Time vs Thread Count (지정 폴더 저장 적용)
    # --------------------------------------------------------
    print("📈 [Figure 2] 2D 실행 시간 선 그래프 생성 중...")
    plt.figure(figsize=(12, 8))
    for c_idx, chunk in enumerate(CHUNK_LIST):
        plt.plot(THREADS_LIST, grid_times[c_idx, :], marker='o', linewidth=2, label=f'CHUNK: {chunk}')
    
    plt.title("Execution Time vs Thread Count")
    plt.xscale('log', base=2)
    plt.xticks(THREADS_LIST, THREADS_LIST)
    plt.xlabel("Number of Threads")
    plt.ylabel("Elapsed Time (seconds)")
    plt.grid(True)
    plt.legend(title="Workload Unit", loc="upper right")
    plt.savefig(os.path.join(output_dir, "Figure2_2D_Time.png"), dpi=300, bbox_inches='tight')
    plt.close()

    # --------------------------------------------------------
    # 4. Figure 3 : Parallel Speedup (지정 폴더 저장 적용)
    # --------------------------------------------------------
    print("🚀 [Figure 3] 2D 병렬 가속비(Speedup) 그래프 생성 중...")
    plt.figure(figsize=(12, 8))
    plt.plot(THREADS_LIST, THREADS_LIST, color='gray', linestyle='--', linewidth=1.5, label='Ideal Speedup')

    plt.ylim(0, 10)

    for c_idx, chunk in enumerate(CHUNK_LIST):
        t1_time = grid_times[c_idx, 0]
        speedup = t1_time / grid_times[c_idx, :]
        plt.plot(THREADS_LIST, speedup, marker='s', linewidth=2, label=f'CHUNK: {chunk}')
    
    plt.title("Parallel Speedup ($S_n = T_1 / T_n$)")
    plt.xscale('log', base=2)
    plt.xticks(THREADS_LIST, THREADS_LIST)
    plt.xlabel("Number of Threads")
    plt.ylabel("Speedup Factor (times)")
    plt.grid(True)
    plt.legend(title="Workload Unit", loc="upper left")
    plt.savefig(os.path.join(output_dir, "Figure3_2D_Speedup.png"), dpi=300, bbox_inches='tight')
    plt.close()

    # --------------------------------------------------------
    # 5. Figure 4 : Heatmap (지정 폴더 저장 적용)
    # --------------------------------------------------------
    print("🔥 [Figure 4] Heatmap 생성 중...")
    fig, ax = plt.subplots(figsize=(12, 8))

    im = ax.imshow(grid_times, cmap='viridis', aspect='auto')

    ax.set_xticks(np.arange(len(THREADS_LIST)))
    ax.set_xticklabels(THREADS_LIST)

    ax.set_yticks(np.arange(len(CHUNK_LIST)))
    ax.set_yticklabels(CHUNK_LIST)

    ax.set_xlabel("Number of Threads")
    ax.set_ylabel("Chunk Size")
    ax.set_title(f"Execution Time Heatmap (MAX={MAX_NUMBER:,})")

    for i in range(len(CHUNK_LIST)):
        for j in range(len(THREADS_LIST)):
            ax.text(j, i, f"{grid_times[i, j]:.2f}", ha='center', va='center', fontsize=8)

    fig.colorbar(im)
    plt.savefig(os.path.join(output_dir, "Figure4_Heatmap.png"), dpi=300, bbox_inches='tight')
    plt.close()

    print(f"\n✨ 대성공! 모든 실험 데이터 표 출력과 그래프 생성이 완료되었습니다.")
    print(f"📁 [저장된 폴더 경로]: {output_dir}/")
    print(f"📌 포함 파일: Figure1_3D_Surface.png, Figure2_2D_Time.png, Figure3_2D_Speedup.png, Figure4_Heatmap.png")

if __name__ == "__main__":
    main()