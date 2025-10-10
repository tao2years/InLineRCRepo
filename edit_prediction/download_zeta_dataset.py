import os
from pathlib import Path
from huggingface_hub import snapshot_download, hf_hub_url
from datasets import load_dataset
from datasets import DatasetDict
from tqdm import tqdm

REPO_ID = "zed-industries/zeta"
REPO_TYPE = "dataset"
OUT_DIR = Path("zeta_full")            # 整库快照目录
EXPORT_DIR = Path("zeta_exports")      # 各 split 导出目录（JSONL/Parquet）

def ensure_dirs():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

def try_snapshot_download():
    print(f"==> 尝试 snapshot_download 拉取整个数据集仓库到: {OUT_DIR.resolve()}")
    local_path = snapshot_download(
        repo_id=REPO_ID,
        repo_type=REPO_TYPE,
        local_dir=str(OUT_DIR),
        local_dir_use_symlinks=False,   # 在 Windows 上用真实文件，避免软链问题
        resume_download=True,           # 断点续传
        max_workers=4,                  # 可按网络情况调大/调小
    )
    print(f"✅ 快照完成: {local_path}")
    return True

def export_with_datasets():
    """
    万一 snapshot_download 被墙/失败，就用 datasets 拉取数据并导出成文件。
    """
    print("==> snapshot_download 失败或你还想顺便导出结构化文件，开始用 datasets 加载并导出")
    
    ds: DatasetDict = load_dataset(REPO_ID)   # type: ignore # 会自动缓存到本地 ~/.cache/huggingface/datasets
    print(f"已加载 splits: {list(ds.keys())}")

    for split_name, split in ds.items():
        # 导出 JSONL
        jsonl_path = EXPORT_DIR / f"{split_name}.jsonl"
        print(f"  -> 导出 {split_name} 为 {jsonl_path} ...")
        split.to_json(str(jsonl_path), orient="records", lines=True)

        # 再导出一份 Parquet，便于快速加载/分析
        pq_path = EXPORT_DIR / f"{split_name}.parquet"
        print(f"  -> 导出 {split_name} 为 {pq_path} ...")
        split.to_parquet(str(pq_path))

    # 简单展示前几条
    for split_name, split in ds.items():
        print(f"\n=== {split_name} 样例（前3条） ===")
        for i in range(min(3, len(split))):
            print(split[i])

def main():
    ensure_dirs()
    ok = False
    try:
        ok = try_snapshot_download()
    except Exception as e:
        print(f"⚠️ snapshot_download 失败：{e}")

    # 不论上一步是否成功，都用 datasets 再导出一份结构化文件，方便你查看与处理
    try:
        export_with_datasets()
    except Exception as e:
        print(f"⚠️ datasets 导出失败：{e}")
        if not ok:
            print("❌ 两种方式都失败了，请检查网络/代理或稍后重试。")

if __name__ == "__main__":
    main()
