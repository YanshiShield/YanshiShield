
import os
import numpy as np
import torch
import torchvision
import torchvision.transforms as transforms


def gen_drichlet_distribution_data(data_path, dataset_name, n_client,
                                   seed, drichlet_arg, print_log=False):
    """Generate data distributed by drichlet.

    Args:
        data_path: where to save download data.
        dataset_name: currently support [mnist, cifar10].
        n_client: The client number, or the number of data will be divided.
        seed: the seed for random. Use same seed, the generated data
              distribution will be the same.
        drichlet_arg: The parameter for drichlet distribution,
                      lower drichlet_arg and higher heterogeneity.
        print_log: if need to print some detail log.
    """
    saved_path = "%s/%s_%d_%d_drichlet%s" % (
        data_path, dataset_name, n_client, seed, drichlet_arg)
    # Prepare data if not ready
    if not os.path.exists(saved_path):
        # Get Raw data                
        if dataset_name == 'mnist':
            trn_load, tst_load = _get_mnist_dataloader(data_path)
            channels = 1
            width = 28
            height = 28
            num_cls = 10
        if dataset_name == 'cifar10':
            trn_load, tst_load = _get_cifar10_dataloader(data_path)
            channels = 3
            width = 32
            height = 32
            num_cls = 10

        trn_x, trn_y, tst_x, tst_y = _load_and_shuffle_data(trn_load,
                                                            tst_load, seed)

        print("start sample from drichlet distribution.")
        clnt_x, clnt_y = _drichlet_distribution(
            trn_x, trn_y, n_client, drichlet_arg,
            channels, width, height, num_cls)

        # Save data
        _save_data(saved_path, clnt_x, clnt_y, tst_x, tst_y)
    else:
        print("Data is already downloaded")
        if dataset_name == 'mnist':
            num_cls = 10
        if dataset_name == 'cifar10':
            num_cls = 10

        clnt_x, clnt_y, tst_x, tst_y = _load_data(saved_path)

    if print_log:
        _print_detail_distribution(clnt_y, tst_y, n_client, num_cls)

    return saved_path, clnt_x, clnt_y, tst_x, tst_y


def _get_mnist_dataloader(data_path):
    transform = transforms.Compose(
        [transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))])
    trnset = torchvision.datasets.MNIST(
        root=data_path, train=True,
        download=True, transform=transform)
    tstset = torchvision.datasets.MNIST(
        root=data_path, train=False,
        download=True, transform=transform)
    
    trn_load = torch.utils.data.DataLoader(
        trnset, batch_size=60000, shuffle=False, num_workers=1)
    tst_load = torch.utils.data.DataLoader(
        tstset, batch_size=10000, shuffle=False, num_workers=1)

    return trn_load, tst_load


def _get_cifar10_dataloader(data_path):
    transform = transforms.Compose(
        [transforms.ToTensor(),
         transforms.Normalize(mean=[0.491, 0.482, 0.447],
                              std=[0.247, 0.243, 0.262])])

    trnset = torchvision.datasets.CIFAR10(
        root=data_path, train=True ,
        download=True, transform=transform)
    tstset = torchvision.datasets.CIFAR10(
        root=data_path, train=False,
        download=True, transform=transform)
    
    trn_load = torch.utils.data.DataLoader(
        trnset, batch_size=50000, shuffle=False, num_workers=1)
    tst_load = torch.utils.data.DataLoader(
        tstset, batch_size=10000, shuffle=False, num_workers=1)

    return trn_load, tst_load


def _load_and_shuffle_data(trn_load, tst_load, seed):
    trn_itr = trn_load.__iter__(); tst_itr = tst_load.__iter__() 
    # labels are of shape (n_data,)
    trn_x, trn_y = trn_itr.__next__()
    tst_x, tst_y = tst_itr.__next__()

    trn_x = trn_x.numpy(); trn_y = trn_y.numpy().reshape(-1,1)
    tst_x = tst_x.numpy(); tst_y = tst_y.numpy().reshape(-1,1)

    # Shuffle Data
    np.random.seed(seed)
    rand_perm = np.random.permutation(len(trn_y))
    trn_x = trn_x[rand_perm]
    trn_y = trn_y[rand_perm]

    return trn_x, trn_y, tst_x, tst_y


def _drichlet_distribution(trn_x, trn_y, n_client, drichlet_arg,
                           channels, width, height, num_cls):
    n_data_per_clnt = int((len(trn_y)) / n_client)
    # Draw from lognormal distribution
    clnt_data_list = (np.random.lognormal(mean=np.log(n_data_per_clnt),
                                          sigma=0, size=n_client))
    clnt_data_list = (clnt_data_list/np.sum(clnt_data_list) * len(
        trn_y)).astype(int)
    diff = np.sum(clnt_data_list) - len(trn_y)

    # Add/Subtract the excess number starting from first client
    if diff!= 0:
        for clnt_i in range(n_client):
            if clnt_data_list[clnt_i] > diff:
                clnt_data_list[clnt_i] -= diff
                break

    cls_priors   = np.random.dirichlet(alpha=[drichlet_arg] * num_cls,
                                       size=n_client)
    prior_cumsum = np.cumsum(cls_priors, axis=1)
    idx_list = [np.where(trn_y==i)[0] for i in range(num_cls)]
    cls_amount = [len(idx_list[i]) for i in range(num_cls)]

    clnt_x = [np.zeros((clnt_data_list[clnt__], channels,
                        height, width)).astype(np.float32)
              for clnt__ in range(n_client)]
    clnt_y = [np.zeros((clnt_data_list[clnt__], 1)).astype(np.int64)
              for clnt__ in range(n_client) ]

    while(np.sum(clnt_data_list)!=0):
        curr_clnt = np.random.randint(n_client)
        # If current node is full resample a client
#         print('Remaining Data: %d' %np.sum(clnt_data_list))
        if clnt_data_list[curr_clnt] <= 0:
            continue
        clnt_data_list[curr_clnt] -= 1
        curr_prior = prior_cumsum[curr_clnt]
        while True:
            cls_label = np.argmax(np.random.uniform() <= curr_prior)
            # Redraw class label if trn_y is out of that class
            if cls_amount[cls_label] <= 0:
                continue
            cls_amount[cls_label] -= 1

            clnt_x[curr_clnt][clnt_data_list[curr_clnt]] = trn_x[idx_list[
                cls_label][cls_amount[cls_label]]]
            clnt_y[curr_clnt][clnt_data_list[curr_clnt]] = trn_y[idx_list[
                cls_label][cls_amount[cls_label]]]
            break

    clnt_x = np.asarray(clnt_x)
    clnt_y = np.asarray(clnt_y)

    return clnt_x, clnt_y


def _save_data(saved_path, clnt_x, clnt_y, tst_x, tst_y):
    os.mkdir(saved_path)

    np.save('%s/clnt_x.npy' % saved_path, clnt_x)
    np.save('%s/clnt_y.npy' % saved_path, clnt_y)

    np.save('%s/tst_x.npy'  % saved_path,  tst_x)
    np.save('%s/tst_y.npy'  % saved_path,  tst_y)


def _load_data(saved_path):
    clnt_x = np.load('%s/clnt_x.npy' % saved_path,
                     allow_pickle=True)
    clnt_y = np.load('%s/clnt_y.npy' % saved_path,
                     allow_pickle=True)

    tst_x  = np.load('%s/tst_x.npy'  % saved_path,
                     allow_pickle=True)
    tst_y  = np.load('%s/tst_y.npy'  % saved_path,
                     allow_pickle=True)

    return clnt_x, clnt_y, tst_x, tst_y


def _print_detail_distribution(clnt_y, tst_y, n_client, num_cls):
    print('Class frequencies:')
    count = 0
    for clnt in range(n_client):
        print("Client %3d: %s, Amount:%d" % (
            clnt,
            ', '.join(["%.3f" % np.mean(
                clnt_y[clnt]==cls) for cls in range(num_cls)]),
            clnt_y[clnt].shape[0]))
        count += clnt_y[clnt].shape[0]

    print('Total Amount: %d' %count)
    print('--------')
    print("      Test: %s, Amount:%d" % (
        ', '.join(["%.3f" % np.mean(tst_y==cls) for cls in range(num_cls)]),
         tst_y.shape[0]))


if __name__ == "__main__":
    gen_drichlet_distribution_data("/tmp/feddc", "cifar10", 10,
                                   20, 0.3, print_log=True)
