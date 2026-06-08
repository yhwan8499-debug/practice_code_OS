import os
import re
import subprocess
import matplotlib.pyplot as plt
import numpy as np

# ==========================================
# 🧪 1. 실험 매크로 설정 구역
# ==========================================
THREADS_LIST = [1, 2, 4, 5, 8, 10, 12, 16, 32, 64, 128]        # X축 스펙
CHUNK_LIST = [1, 10, 100, 1000, 10000, 100000, 1000000, 5000000, 10000000] # Y축 스펙
MAX_NUMBER = 50000000                       # 탐색 상한선 (이 값에 따라 폴더가 생성됩니다)
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
    
    # --------------------------------------------------------
    # 💻 💡 기기별 결과 분리 구역 (데스크톱용 폴더명 설정)
    # --------------------------------------------------------
    ENV_NAME = "laptop"  # 노트북에서 할 때는 "laptop"으로 변경하시면 됩니다.
    output_dir = f"{ENV_NAME}_result_{MAX_NUMBER}_ex"
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
    # 1. 보고서용 마크다운 표 출력 및 파일 자동 저장 구역 ★
    # --------------------------------------------------------
    print("\n" + "="*60)
    print("📊 보고서에 그대로 복사해서 넣을 마크다운 표 결과")
    print("="*60)
    
    # 텍스트 파일로 내보낼 마크다운 문자열 생성
    md_table_content = "| CHUNK_SIZE | NUM_THREADS | 평균 수행 시간 (Elapsed Time) |\n"
    md_table_content += "| :--- | :--- | :--- |\n"
    
    for c_idx, chunk in enumerate(CHUNK_LIST):
        for t_idx, thread in enumerate(THREADS_LIST):
            md_table_content += f"| {chunk} | {thread}개 | {grid_times[c_idx, t_idx]:.4f} s |\n"
            
    # 터미널 창에 표 시각화
    print(md_table_content)
    print("="*60)

    # 📁 1-1. 마크다운 표를 텍스트 파일(.txt)로 저장
    txt_output_path = os.path.join(output_dir, "report_table.txt")
    with open(txt_output_path, "w", encoding="utf-8") as f:
        f.write(md_table_content)
    print(f"📝 마크다운 표 파일 저장 완료: {txt_output_path}")

    # 📁 1-2. 엑셀 연동용 CSV 파일로 저장
    csv_output_path = os.path.join(output_dir, "benchmark_data.csv")
    with open(csv_output_path, "w", encoding="utf-8") as f:
        f.write("CHUNK_SIZE,NUM_THREADS,Elapsed_Time(s)\n")
        for c_idx, chunk in enumerate(CHUNK_LIST):
            for t_idx, thread in enumerate(THREADS_LIST):
                f.write(f"{chunk},{thread},{grid_times[c_idx, t_idx]:.4f}\n")
    print(f"📊 CSV 데이터 파일 저장 완료: {csv_output_path}")

    # 시각화용 Grid Mesh 생성
    X_mesh, Y_mesh = np.meshgrid(THREADS_LIST, CHUNK_LIST)

    # --------------------------------------------------------
    # 2. Figure 1 : 3D Surface
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

    ax.set_title(f"Execution Time Surface ({ENV_NAME.upper()} MAX={MAX_NUMBER:,})", fontsize=14)
    ax.set_xlabel("Threads")
    ax.set_ylabel("Chunk Size")
    ax.set_zlabel("Time (s)")

    tick_chunks = [1, 10, 100, 1000, 10000, 100000, 1000000, 10000000]
    ax.set_yticks([np.log10(x) for x in tick_chunks])
    ax.set_yticklabels([str(x) for x in tick_chunks])

    ax.view_init(elev=30, azim=-45)
    fig.colorbar(surf, shrink=0.6, aspect=12)
    
    plt.savefig(os.path.join(output_dir, "Figure1_3D_Surface.png"), dpi=300, bbox_inches='tight')
    plt.close()

    # --------------------------------------------------------
    # 3. Figure 2 : Execution Time vs Thread Count
    # --------------------------------------------------------
    print("📈 [Figure 2] 2D 실행 시간 선 그래프 생성 중...")
    plt.figure(figsize=(12, 8))
    for c_idx, chunk in enumerate(CHUNK_LIST):
        plt.plot(THREADS_LIST, grid_times[c_idx, :], marker='o', linewidth=2, label=f'CHUNK: {chunk}')
    
    plt.title(f"Execution Time vs Thread Count ({ENV_NAME.upper()})")
    plt.xscale('log', base=2)
    plt.xticks(THREADS_LIST, THREADS_LIST)
    plt.xlabel("Number of Threads")
    plt.ylabel("Elapsed Time (seconds)")
    plt.grid(True)
    plt.legend(title="Workload Unit", loc="upper right")
    plt.savefig(os.path.join(output_dir, "Figure2_2D_Time.png"), dpi=300, bbox_inches='tight')
    plt.close()

    # --------------------------------------------------------
    # 4. Figure 3 : Parallel Speedup
    # --------------------------------------------------------
    print("🚀 [Figure 3] 2D 병렬 가속비(Speedup) 그래프 생성 중...")
    plt.figure(figsize=(12, 8))
    plt.plot(THREADS_LIST, THREADS_LIST, color='gray', linestyle='--', linewidth=1.5, label='Ideal Speedup')

    plt.ylim(0, 10)

    for c_idx, chunk in enumerate(CHUNK_LIST):
        t1_time = grid_times[c_idx, 0]
        speedup = t1_time / grid_times[c_idx, :]
        plt.plot(THREADS_LIST, speedup, marker='s', linewidth=2, label=f'CHUNK: {chunk}')
    
    plt.title(f"Parallel Speedup ($S_n = T_1 / T_n$) ({ENV_NAME.upper()})")
    plt.xscale('log', base=2)
    plt.xticks(THREADS_LIST, THREADS_LIST)
    plt.xlabel("Number of Threads")
    plt.ylabel("Speedup Factor (times)")
    plt.grid(True)
    plt.legend(title="Workload Unit", loc="upper left")
    plt.savefig(os.path.join(output_dir, "Figure3_2D_Speedup.png"), dpi=300, bbox_inches='tight')
    plt.close()

    # --------------------------------------------------------
    # 5. Figure 4 : Heatmap
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
    ax.set_title(f"Execution Time Heatmap ({ENV_NAME.upper()} MAX={MAX_NUMBER:,})")

    for i in range(len(CHUNK_LIST)):
        for j in range(len(THREADS_LIST)):
            ax.text(j, i, f"{grid_times[i, j]:.2f}", ha='center', va='center', fontsize=8)

    fig.colorbar(im)
    plt.savefig(os.path.join(output_dir, "Figure4_Heatmap.png"), dpi=300, bbox_inches='tight')
    plt.close()

    print(f"\n✨ 대성공! 모든 실험 데이터 표 출력과 그래프 생성이 완료되었습니다.")
    print(f"📁 [저장된 폴더 경로]: {output_dir}/")
    print(f"📌 포함 파일: Figure1~4 이미지, report_table.txt(보고서용 표), benchmark_data.csv(엑셀용 데이터)")

if __name__ == "__main__":
    main()