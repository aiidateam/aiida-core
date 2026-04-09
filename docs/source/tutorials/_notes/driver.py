import subprocess
import sys
import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import yaml


def save_pattern_png(V, filename, cmap='inferno'):
    if V.ndim != 2:
        raise ValueError('V must be a 2D array')

    plt.figure(figsize=(4, 4))
    plt.imshow(V, cmap=cmap, origin='lower')
    plt.axis('off')
    plt.tight_layout(pad=0)
    plt.savefig(filename, dpi=200)
    plt.close()


def run_reaction_diffusion_scan():
    # --- Working directory ---
    workdir = Path(tempfile.mkdtemp())
    print(f'Work dir: {workdir}')

    input_file = workdir / 'input.yaml'
    output_file = workdir / 'results.npz'

    # --- Fixed parameters ---
    base_params = {
        'grid_size': 128,
        'du': 0.16,
        'dv': 0.08,
        'k': 0.065,
        'dt': 1.0,
        'n_steps': 5000,
        'seed': 42,
    }

    # --- Scan parameter ---
    F_values = np.linspace(0.035, 0.05, 20)

    # --- Collected results ---
    variances = []
    means = []
    successful_F = []
    image_files = []

    for idx, F in enumerate(F_values):
        print(f'Running F = {F:.4f}')

        params = base_params.copy()
        params['F'] = float(F)

        image_file = workdir / f'pattern-{idx:03d}.png'

        # --- Write input file ---
        with open(input_file, 'w') as f:
            yaml.safe_dump(params, f)

        # --- Run executable ---
        script_dir = Path(__file__).parent

        result = subprocess.run(
            [
                sys.executable,
                str(script_dir / 'reaction-diffusion.py'),
                # "./reaction-diffusion.py",
                '--input',
                str(input_file),
                '--output',
                str(output_file),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            print(f'  FAILED (exit code {result.returncode})')
            print(result.stderr.strip())
            variances.append(np.nan)
            means.append(np.nan)
            continue

        if 'JOB DONE' not in result.stdout:
            print('  FAILED (no success marker)')
            variances.append(np.nan)
            means.append(np.nan)
            continue

        # --- Load outputs ---
        data = np.load(output_file)
        V = data['V_final']
        var_v = float(data['variance_V'])
        mean_v = float(data['mean_V'])

        variances.append(var_v)
        means.append(mean_v)
        successful_F.append(F)

        # --- Save image ---
        save_pattern_png(V, image_file)
        image_files.append(image_file)

        print(f'  variance(V) = {var_v:.4e}')

    # -------------------------
    # Plot 1: variance vs F
    # -------------------------
    plt.figure(figsize=(5, 4))
    plt.plot(F_values, variances, marker='o')
    plt.xlabel('Feed rate F')
    plt.ylabel('Variance of V')
    plt.title('Pattern strength vs feed rate')
    plt.tight_layout()
    plt.savefig(workdir / 'variance_vs_F.png', dpi=200)
    plt.close()

    # -------------------------
    # Plot 2 (optional): mean vs F
    # -------------------------
    plt.figure(figsize=(5, 4))
    plt.plot(F_values, means, marker='o')
    plt.xlabel('Feed rate F')
    plt.ylabel('Mean of V')
    plt.title('Mean concentration vs feed rate')
    plt.tight_layout()
    plt.savefig(workdir / 'mean_vs_F.png', dpi=200)
    plt.close()

    # -------------------------
    # Plot 3: representative patterns
    # -------------------------
    if image_files:
        n_show = min(4, len(image_files))
        indices = np.linspace(0, len(image_files) - 1, n_show, dtype=int)

        fig, axes = plt.subplots(1, n_show, figsize=(4 * n_show, 4))
        if n_show == 1:
            axes = [axes]

        for ax, i in zip(axes, indices):
            img = plt.imread(image_files[i])
            ax.imshow(img)
            ax.set_title(f'F = {successful_F[i]:.3f}')
            ax.axis('off')

        plt.tight_layout()
        plt.savefig(workdir / 'representative_patterns.png', dpi=200)
        plt.close()

    print('\nScan complete.')
    print(f'Results written to: {workdir}')


if __name__ == '__main__':
    run_reaction_diffusion_scan()
