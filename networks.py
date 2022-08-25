"""
AI Fashion Coordinator
(Baseline For Fashion-How Challenge)

MIT License

Copyright (C) 2022, Integrated Intelligence Research Section, ETRI

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Update: 2022.04.20.
"""
import torch.nn as nn
import torchvision.models as models
import torch

### 라이브러리 설치 ####
import subprocess
import sys

try:
    from efficientnet_pytorch import EfficientNet
except ImportError:
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "efficientnet_pytorch"]
    )
finally:
    from efficientnet_pytorch import EfficientNet
##########################


class ResExtractor(nn.Module):
    """Feature extractor based on ResNet structure
        Selectable from resnet18 to resnet152

    Args:
        resnetnum: Desired resnet version
                    (choices=['18','34','50','101','152'])
        pretrained: 'True' if you want to use the pretrained weights provided by Pytorch,
                    'False' if you want to train from scratch.
    """

    def __init__(self, resnetnum="50", pretrained=True):
        super(ResExtractor, self).__init__()

        if resnetnum == "18":
            self.resnet = models.resnet18(pretrained=pretrained)
        elif resnetnum == "34":
            self.resnet = models.resnet34(pretrained=pretrained)
        elif resnetnum == "50":
            self.resnet = models.resnet50(pretrained=pretrained)
        elif resnetnum == "101":
            self.resnet = models.resnet101(pretrained=pretrained)
        elif resnetnum == "152":
            self.resnet = models.resnet152(pretrained=pretrained)

        self.modules_front = list(self.resnet.children())[:-2]
        self.model_front = nn.Sequential(*self.modules_front)

    def front(self, x):
        """In the resnet structure, input 'x' passes through conv layers except for fc layers."""
        return self.model_front(x)


class Baseline_ResNet_emo(nn.Module):
    """Classification network of emotion categories based on ResNet18 structure."""

    def __init__(self):
        super(Baseline_ResNet_emo, self).__init__()

        self.encoder = ResExtractor("18")
        self.avg_pool = nn.AvgPool2d(kernel_size=7)

        self.daily_linear = nn.Linear(512, 7)
        self.gender_linear = nn.Linear(512, 6)
        self.embel_linear = nn.Linear(512, 3)

    def forward(self, x):
        """Forward propagation with input 'x'"""
        feat = self.encoder.front(x["image"])
        flatten = self.avg_pool(feat).squeeze()

        out_daily = self.daily_linear(flatten)
        out_gender = self.gender_linear(flatten)
        out_embel = self.embel_linear(flatten)

        return out_daily, out_gender, out_embel


class EfficientNet_emo(nn.Module):
    def __init__(self):
        super(EfficientNet_emo, self).__init__()
        model = EfficientNet.from_pretrained("efficientnet-b1")
        tmp = list(model.children())[:-4]
        self.enc = nn.Sequential(tmp[0], tmp[1], *tmp[2], *tmp[3:])

        nc = list(model.children())[-2].in_features
        self.head = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(nc, 512),
            nn.BatchNorm1d(512),
            nn.Dropout(),
        )
        self.daily_linear = nn.Linear(512, 7)
        self.gender_linear = nn.Linear(512, 6)
        self.embel_linear = nn.Linear(512, 3)

    def forward(self, x):
        x = self.enc(x["image"])
        x = self.head(x)

        out_daily = self.daily_linear(x)
        out_gender = self.gender_linear(x)
        out_embel = self.embel_linear(x)

        return out_daily, out_gender, out_embel


class EfficientNetV2_emo(nn.Module):
    def __init__(self):
        super(EfficientNetV2_emo, self).__init__()
        model = torch.hub.load(
            "hankyul2/EfficientNetV2-pytorch",
            "efficientnet_v2_l",
            pretrained=True,
            nclass=1,
        )
        tmp = list(model.children())
        nc = list(model.children())[2][-1].in_features

        self.stem = tmp[0]
        self.blocks = tmp[1]

        self.head = nn.Sequential(
            tmp[2][0],
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten(),
            nn.Dropout(p=0.1, inplace=True),
        )

        self.daily_linear = nn.Linear(nc, 7)
        self.gender_linear = nn.Linear(nc, 6)
        self.embel_linear = nn.Linear(nc, 3)

    def forward(self, x):
        x = self.stem(x["image"])
        x = self.blocks(x)
        x = self.head(x)

        out_daily = self.daily_linear(x)
        out_gender = self.gender_linear(x)
        out_embel = self.embel_linear(x)

        return out_daily, out_gender, out_embel


# 버전을 입력받으면 그에 맞게 EfficientNet-b0 ~ b7, v2까지 구현할 예정입니다.
# class EfficientNet_emo(nn.Module):
#     def __init__(self, pretrained=True):
#         super().__init__()

#         model = EfficientNet.from_pretrained("efficientnet-b1")
#         # print(model)
#         self.enc = model
#         # print(self.enc)

#         nc = list(model.children())[-2].in_features
#         self.head = nn.Sequential(
#             nn.AdaptiveAvgPool2d(1),
#             nn.Flatten(),
#             nn.Linear(nc, 512),
#             nn.BatchNorm1d(512),
#             nn.Dropout(),
#         )
#         self.daily_linear = nn.Linear(512, 7)
#         self.gender_linear = nn.Linear(512, 6)
#         self.embel_linear = nn.Linear(512, 3)

#     def forward(self, x):
#         x = self.enc.extract_features(x["image"])
#         x = self.head(x)

#         out_daily = self.daily_linear(x)
#         out_gender = self.gender_linear(x)
#         out_embel = self.embel_linear(x)

#         return out_daily, out_gender, out_embel

if __name__ == "__main__":
    pass
