import torch
from torch import nn

from . import common
import numpy as np


class Masksembles2D(nn.Module):
    """
    :class:`Masksembles2D` is high-level class that implements Masksembles approach
    for 2-dimensional inputs (similar to :class:`torch.nn.Dropout2d`).

    :param channels: int, number of channels used in masks.
    :param n: int, number of masks
    :param scale: float, scale parameter similar to *S* in [1]. Larger values decrease \
        subnetworks correlations but at the same time decrease capacity of every individual model.

    Shape:
        * Input: (N, C, H, W)
        * Output: (N, C, H, W) (same shape as input)

    Examples:

    >>> m = Masksembles2D(16, 4, 2.0)
    >>> input = torch.ones([4, 16, 28, 28])
    >>> output = m(input)

    References:

    [1] `Masksembles for Uncertainty Estimation`,
    Nikita Durasov, Timur Bagautdinov, Pierre Baque, Pascal Fua

    """

    def __init__(
        self,
        channels: int,
        n: int,
        scale: float,
        generate_masks: bool = True,
        nested_masks: bool = False,
    ):
        super().__init__()

        self.channels = channels
        self.n = n
        self.scale = scale

        if generate_masks:
            masks = common.generation_wrapper(channels, n, scale)
            masks = torch.from_numpy(masks)

            if nested_masks:
                for i in range(1, n):
                    masks[i] = np.logical_or(masks[i], masks[i - 1])
            self.masks = torch.nn.Parameter(masks, requires_grad=False).double()

        else:
            masks = np.zeros([n, channels])
            masks = torch.from_numpy(masks)
            self.masks = torch.nn.Parameter(masks, requires_grad=False).double()

    def forward(self, inputs):
        batch = inputs.shape[0]
        x = torch.split(inputs.unsqueeze(1), batch // self.n, dim=0)
        x = torch.cat(x, dim=1).permute([1, 0, 2, 3, 4])
        x = x * self.masks.unsqueeze(1).unsqueeze(-1).unsqueeze(-1)
        x = torch.cat(torch.split(x, 1, dim=0), dim=1)
        return x.squeeze(0).float()


class Masksembles1D(nn.Module):
    """
    :class:`Masksembles1D` is high-level class that implements Masksembles approach
    for 1-dimensional inputs (similar to :class:`torch.nn.Dropout`).

    :param channels: int, number of channels used in masks.
    :param n: int, number of masks
    :param scale: float, scale parameter similar to *S* in [1]. Larger values decrease \
        subnetworks correlations but at the same time decrease capacity of every individual model.

    Shape:
        * Input: (N, C)
        * Output: (N, C) (same shape as input)

    Examples:

    >>> m = Masksembles1D(16, 4, 2.0)
    >>> input = torch.ones([4, 16])
    >>> output = m(input)


    References:

    [1] `Masksembles for Uncertainty Estimation`,
    Nikita Durasov, Timur Bagautdinov, Pierre Baque, Pascal Fua

    """

    def __init__(
        self,
        channels: int,
        n: int,
        scale: float,
        generate_masks: bool = True,
        nested_masks: bool = False,
    ):
        super().__init__()

        self.channels = channels
        self.n = n
        self.scale = scale

        if generate_masks:
            if scale == 1:
                masks = np.ones([n, channels])
            else:
                masks = common.generation_wrapper(channels, n, scale)

            masks = torch.from_numpy(masks)
            if nested_masks:
                for i in range(1, n):
                    masks[i] = np.logical_or(masks[i], masks[i - 1])
            self.masks = torch.nn.Parameter(masks, requires_grad=False).double()
        else:
            masks = np.zeros([n, channels])
            masks = torch.from_numpy(masks)
            self.masks = torch.nn.Parameter(masks, requires_grad=False).double()

    def forward(self, inputs):
        batch = inputs.shape[0]
        x = torch.split(inputs.unsqueeze(1), batch // self.n, dim=0)
        x = torch.cat(x, dim=1).permute([1, 0, 2])
        x = x * self.masks.unsqueeze(1)
        x = torch.cat(torch.split(x, 1, dim=0), dim=1)
        return x.squeeze(0).float()


class Masksembles1DDynamicSize(nn.Module):
    def __init__(
        self,
        channels: int,
        n: int,
        scale: float,
        generate_masks: bool = True,
    ):
        super().__init__()

        self.channels = channels
        self.n = n
        self.scale = scale
        self.expected_size = int(channels * scale * (1 - (1 - 1 / scale) ** n))

        if generate_masks:
            masks = common.generate_masks(channels, n, scale)
            masks = torch.from_numpy(masks)
            self.masks = torch.nn.Parameter(masks, requires_grad=False).double()
        else:
            masks = np.zeros([n, self.expected_size])
            masks = torch.from_numpy(masks)
            self.masks = torch.nn.Parameter(masks, requires_grad=False).double()

    def forward(self, inputs):
        batch = inputs.shape[0]
        x = torch.split(inputs.unsqueeze(1), batch // self.n, dim=0)
        x = torch.cat(x, dim=1).permute([1, 0, 2])
        x = x * self.masks.unsqueeze(1)
        x = torch.cat(torch.split(x, 1, dim=0), dim=1)
        return x.squeeze(0).float()


class Masksembles2DDynamicSize(nn.Module):
    """
    :class:`Masksembles2D` is high-level class that implements Masksembles approach
    for 2-dimensional inputs (similar to :class:`torch.nn.Dropout2d`).

    :param channels: int, number of channels used in masks.
    :param n: int, number of masks
    :param scale: float, scale parameter similar to *S* in [1]. Larger values decrease \
        subnetworks correlations but at the same time decrease capacity of every individual model.

    Shape:
        * Input: (N, C, H, W)
        * Output: (N, C, H, W) (same shape as input)

    Examples:

    >>> m = Masksembles2D(16, 4, 2.0)
    >>> input = torch.ones([4, 16, 28, 28])
    >>> output = m(input)

    References:

    [1] `Masksembles for Uncertainty Estimation`,
    Nikita Durasov, Timur Bagautdinov, Pierre Baque, Pascal Fua

    """

    def __init__(
        self,
        channels: int,
        n: int,
        scale: float,
        generate_masks: bool = True,
    ):
        super().__init__()

        self.channels = channels
        self.n = n
        self.scale = scale
        self.expected_size = int(channels * scale * (1 - (1 - 1 / scale) ** n))

        if generate_masks:
            masks = common.generate_masks(channels, n, scale)
            masks = torch.from_numpy(masks)
            self.masks = torch.nn.Parameter(masks, requires_grad=False).double()
        else:
            masks = np.zeros([n, self.expected_size])
            masks = torch.from_numpy(masks)
            self.masks = torch.nn.Parameter(masks, requires_grad=False).double()

    def forward(self, inputs):
        batch = inputs.shape[0]
        x = torch.split(inputs.unsqueeze(1), batch // self.n, dim=0)
        x = torch.cat(x, dim=1).permute([1, 0, 2, 3, 4])
        x = x * self.masks.unsqueeze(1).unsqueeze(-1).unsqueeze(-1)
        x = torch.cat(torch.split(x, 1, dim=0), dim=1)
        return x.squeeze(0).float()
