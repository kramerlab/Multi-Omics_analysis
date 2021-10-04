import argparse
import sys
from pathlib import Path
import numpy as np
import torch
from sklearn.model_selection import StratifiedKFold
from tqdm import tqdm

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from utils import multi_omics_data
from utils.network_training_util import test, calculate_mean_and_std_auc

from utils.choose_gpu import get_free_gpu
from training_bo_holi_moli import train_final

drugs = {
    'Gemcitabine_tcga': 'TCGA',
    'Gemcitabine_pdx': 'PDX',
    'Cisplatin': 'TCGA',
    'Docetaxel': 'TCGA',
    'Erlotinib': 'PDX',
    'Cetuximab': 'PDX',
    'Paclitaxel': 'PDX',
}

random_seed = 42


def rerun_final_architecture(method_name, experiment_name, gpu_number, drug_name, extern_dataset_name,
                             best_parameters_list):
    torch.manual_seed(random_seed)
    np.random.seed(random_seed)
    cv_splits = 5
    skf = StratifiedKFold(n_splits=cv_splits, random_state=random_seed, shuffle=True)
    if torch.cuda.is_available():
        if gpu_number is None:
            free_gpu_id = get_free_gpu()
        else:
            free_gpu_id = gpu_number
        device = torch.device(f"cuda:{free_gpu_id}")
        pin_memory = False
    else:
        device = torch.device("cpu")
        pin_memory = False

    if experiment_name is None:
        result_path = Path('..', '..', '..', 'results', 'bayesian_optimisation', drug_name, method_name)
    else:
        result_path = Path('..', '..', '..', 'results', 'bayesian_optimisation', drug_name, experiment_name)
    result_path.mkdir(parents=True, exist_ok=True)

    result_file = open(result_path / 'rerun_results.txt', 'w')
    result_file.write(f"Start for {drug_name}\n")
    print(f"Start for {drug_name}")

    data_path = Path('..', '..', '..', 'data')
    gdsc_e, gdsc_m, gdsc_c, gdsc_r, extern_e, extern_m, extern_c, extern_r \
        = multi_omics_data.load_drug_data(data_path, drug_name, extern_dataset_name)

    iteration = 0
    auc_list_test = []
    auprc_list_test = []
    auc_list_extern = []
    auprc_list_extern = []
    for train_index, test_index in tqdm(skf.split(gdsc_e, gdsc_r), total=skf.get_n_splits(), desc=" Outer k-fold"):
        x_train_e = gdsc_e[train_index]
        x_train_m = gdsc_m[train_index]
        x_train_c = gdsc_c[train_index]
        y_train = gdsc_r[train_index]
        x_test_e = gdsc_e[test_index]
        x_test_m = gdsc_m[test_index]
        x_test_c = gdsc_c[test_index]
        y_test = gdsc_r[test_index]

        model_final, scaler_final = train_final(best_parameters_list[iteration], x_train_e, x_train_m, x_train_c,
                                                y_train, device, pin_memory)
        auc_test, auprc_test = test(model_final, scaler_final, x_test_e, x_test_m, x_test_c, y_test, device,
                                    pin_memory)
        auc_list_test.append(auc_test)
        auprc_list_test.append(auprc_test)

        auc_extern, auprc_extern = test(model_final, scaler_final, extern_e, extern_m, extern_c,
                                        extern_r, device, pin_memory)
        auc_list_extern.append(auc_extern)
        auprc_list_extern.append(auprc_extern)
        iteration += 1

    result_dict = {
        'test auroc': auc_list_test,
        'test_auprc': auprc_list_test,
        'extern auroc': auc_list_extern,
        'extern auprc': auprc_list_extern
    }

    calculate_mean_and_std_auc(result_dict, result_file, drug_name)

    positive_extern = np.count_nonzero(extern_r == 1)
    negative_extern = np.count_nonzero(extern_r == 0)
    no_skill_prediction_auprc = positive_extern / (positive_extern + negative_extern)
    result_file.write(f'\n No skill predictor extern AUPRC: {no_skill_prediction_auprc} \n')
    result_file.write(f'\n test auroc list: {auc_list_test} \n')
    result_file.write(f'\n test auprc list: {auprc_list_test} \n')
    result_file.write(f'\n extern auroc list: {auc_list_extern} \n')
    result_file.write(f'\n extern auprc list: {auprc_list_extern} \n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--gpu_number', type=int)
    parser.add_argument('--method_name', required=True)
    parser.add_argument('--experiment_name', required=False, default=None)
    args = parser.parse_args()

    p = Path('../results')
    logfile_name = 'logs.txt'
    cv_result_path = Path('..', '..', '..', 'results', 'bayesian_optimisation')

    drug_paths = [x for x in cv_result_path.iterdir()]
    for drug_path in drug_paths:
        best_parameters_list = []
        drug_name = drug_path.stem
        if drug_name in ('EGFR', 'ensemble'):
            continue
        log_path = drug_path / args.method_name / logfile_name
        if log_path.is_file():
            with open(log_path, 'r') as log_file:
                test_auroc = []
                extern_auroc = []
                for line in log_file:
                    if 'best_parameters' in line:
                        best_parameter_string = line.split("=")[-1].strip()
                        # strip the string literals
                        best_parameters_list.append(eval(best_parameter_string[1:-1]))

        rerun_final_architecture(args.method_name, args.experiment_name, args.gpu_number, drug_name, drugs[drug_name],
                                 best_parameters_list)
