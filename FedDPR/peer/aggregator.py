import torch
from FedDPR.utils.btbcn import BinaryClusterTree

class Aggregator:
    def __init__(self, n, m, method, device, **kwargs):
        self.n = n
        self.m = m
        self.method = method
        self.device = device
        for k, v in kwargs.items():
            setattr(self, k, v)
        if method == 'bds' and self.is_server:
            self.fwd_scores = torch.rand(self.n).to(self.device)
            
    def set_local_grad(self, local_grad: torch.Tensor):
        self.local_grad = local_grad.clone()
        
    def get_fwd_scores(self):
        return self.fwd_scores    
        
    def get_bwd_scores(self):
        return self.bwd_scores
    
    def update_fwd_scores(self, bwd_scores: torch.Tensor):
        pred = self.z_score_detect(bwd_scores, 1)
        mult = torch.where(pred, self.penalty, 1)
        add = torch.where(pred, 0, 1)
        # print(diffs)
        self.fwd_scores *= mult
        self.fwd_scores += add
        
        
    def aggregate(self, grads: torch.Tensor):
        grads = grads.clone()
        match self.method:
            case 'none':
                return grads.mean(dim=0)
            case 'median':
                return grads.median(dim=0).values
            case 'trm':
                return self.trimmed_mean(grads)
            case 'krum':
                return self.krum(grads)
            case 'feddmc':
                return self.fed_dmc(grads)
            case 'bds':
                if self.is_server:
                    return self.bds_server(grads)
                else:
                    return self.bds_client(grads)
            case 'collusion':
                return self.collude(grads)
    
    def collude(self, grads: torch.Tensor):
        grads_g = grads[torch.randint(0, self.m, (1,))].squeeze()
        print('||grads_g|| = ', grads_g.norm(dim=0))
        return grads_g
    
    def trimmed_mean(self, grads: torch.Tensor, prop=0.8):
        k = int(grads.shape[0] * prop)
        sorted_grads, _ = torch.sort(grads, dim=0)
        trimmed_grads = sorted_grads[k : -k, :]
        return torch.mean(trimmed_grads, dim=0)
    
    def krum(self, grads: torch.Tensor):
        dist_mat = torch.cdist(grads, grads)
        dist_vec = torch.sum(dist_mat, dim=1)
        target = torch.argmin(dist_vec)
        return grads[target].squeeze()
    
    def fed_dmc(self, grads: torch.Tensor, k=5, min_clu_size=2):
        u_mat, s_mat, _ = torch.pca_lowrank(grads, q=k)
        x_proj = u_mat.matmul(torch.diag(s_mat)).to('cpu')
        bct = BinaryClusterTree(min_clu_size)
        bct.fit(x_proj)
        benign, _, _ = bct.classify()
        
        return torch.mean(grads[benign], dim=0)
    
    def bds_server(self, grads: torch.Tensor): 
        norm1 = grads.norm(dim=1)
        print(f'grads norm: {norm1} @ {norm1.shape}')    
        weights = (self.fwd_scores / self.fwd_scores.sum()).unsqueeze(-1)
        grad_g = torch.sum(grads * weights, dim=0)
        norm2 = grad_g.norm()
        print('grad_g norm:', norm2, ' @ ', {norm2.shape})
        return grad_g
    
    def bds_client(self, grads: torch.Tensor):
        prod = grads.matmul(self.local_grad)
        norm1 = grads.norm(p=2, dim=1)
        norm2 = self.local_grad.norm(p=2)
        
        cos_sim = self.normalize(torch.exp(prod / (norm1 * norm2)))
        norm_sim = 1 - torch.abs(norm1 - norm2) / (norm1 + norm2)
        self.bwd_scores = norm_sim * cos_sim
        inliers = self.z_score_detect(self.bwd_scores, 1, inlier=True)
        print(inliers)
        return torch.mean(grads[inliers], dim=0)
    
    @staticmethod
    def normalize(x: torch.Tensor):
        return x / torch.sum(x)
    
    @staticmethod
    def z_score_detect(x: torch.Tensor, thr=3, inlier=False):
        z_scores = (x - x.mean()) / x.std()
        if inlier:
            return torch.abs(z_scores) <= thr
        else:
            return torch.abs(z_scores) > thr