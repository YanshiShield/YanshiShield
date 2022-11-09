
import argparse

import torch
import neursafe_fl as nsfl
from train import load_data, LeNetModel, test


device = 'cuda' if torch.cuda.is_available() else 'cpu'


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--client_index", required=False, type=int,
                        help="The client index")
    parser.add_argument("--data_path", required=False,
                        help="The path saved data which sampled from drichlet")
    args = parser.parse_args()

    _, _, tst_x, tst_y = load_data(args.data_path)
    net = LeNetModel()
    
    nsfl.load_weights(net)
    net = net.to(device)

    loss, accuracy = test(net, tst_x, tst_y)
    metrics = {
        'sample_num': tst_x.shape[0],
        'loss': loss,
        'accuracy': accuracy
    }
    print(metrics)
    nsfl.commit(metrics)
