import torch
import argparse
import os
import tqdm
import copy


column_weight = [
    "lm_head.weight",
    "wte.weight",
    "mlp.w1.weight",
    "mlp.w2.weight",
    "c_attn.weight",
]

row_weight = [
    "attn.c_proj.weight",
    "mlp.c_proj.weight",
]

column_bias = [
    "c_attn.bias"
]

no_mp_weights = [
    "ln_1.weight",
    "ln_2.weight",
    "ln_f.weight",
]


def increase_mp_qwen(d, mp_size, half=False):

    print("Increase MP size.")

    ratio = mp_size
    start = 0
    end = ratio

    ckpts = []

    for j in tqdm.tqdm(range(start, end)):
        d_new = {}
        shift = j - start

        for k, v in d.items():
            assert len(v.shape) < 3
            if any([kk in k for kk in column_weight]):
                part = v.shape[0] // ratio
                d_new[k] = v[shift*part:(shift+1)*part, :].clone()
            elif any([kk in k for kk in row_weight]):
                part = v.shape[1] // ratio
                d_new[k] = v[:, shift*part:(shift+1)*part].clone()
            elif any([kk in k for kk in column_bias]):
                d_new[k] = v[shift*part:(shift+1)*part].clone()
            else:
                assert any([kk in k for kk in no_mp_weights]), k
                d_new[k] = v.clone()

            # print(k, d[k].size(), d[k].dtype, d_new[k].size(), d_new[k].dtype)

        ckpts.append(d_new)

    return ckpts


def decrease_mp_qwen(d_list, half=False):

    print("Decrease MP size to 1.")

    d_new = {}

    for k, v in d_list[0].items():
        assert len(v.shape) < 3
        if any([kk in k for kk in column_weight]):
            d_new[k] = torch.cat([d[k] for d in d_list], dim=0)
        elif any([kk in k for kk in row_weight]):
            d_new[k] = torch.cat([d[k] for d in d_list], dim=1)
        elif any([kk in k for kk in column_bias]):
            d_new[k] = torch.cat([d[k] for d in d_list], dim=0)
        else:
            assert any([kk in k for kk in no_mp_weights]), k
            d_new[k] = v.clone()

    return d_new
