
# check_cuda.py
import torch
import sys

print(f"Python version: {sys.version}")
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    print(f"Number of GPUs: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
    
    # Test CUDA with a simple tensor operation
    print("\nTesting CUDA with tensor operations...")
    x = torch.rand(5, 3).cuda()
    print(f"Tensor on GPU: {x}")
    print(f"Tensor device: {x.device}")
else:
    print("CUDA is not available. Check your PyTorch installation and NVIDIA drivers.")
    print("You might need to reinstall PyTorch with CUDA support.")