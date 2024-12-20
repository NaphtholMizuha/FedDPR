from torchvision import datasets, transforms


def get_imagenette(path: str, train: bool = True):
    if train:
        tf = transforms.Compose(
            [
                transforms.RandomResizedCrop(224),  # 随机裁剪并调整大小
                transforms.RandomHorizontalFlip(),  # 随机水平翻转
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                ),
            ]
        )
    else:
        tf = transforms.Compose(
            [
                transforms.RandomResizedCrop(224),  # 随机裁剪并调整大小
                transforms.RandomHorizontalFlip(),  # 随机水平翻转
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                ),
            ]
        )
    return datasets.ImageFolder(
        root=f"{path}/imagenette2-320/train"
        if train
        else f"{path}/imagenette2-320/val",
        transform=tf,
    )