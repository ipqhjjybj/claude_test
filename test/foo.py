def fibonacci(n):
    """
    生成斐波那契数列的前n个数字
    
    Args:
        n (int): 要生成的斐波那契数字个数
    
    Returns:
        list: 包含前n个斐波那契数字的列表
    """
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    
    fib_sequence = [0, 1]
    for i in range(2, n):
        next_fib = fib_sequence[i-1] + fib_sequence[i-2]
        fib_sequence.append(next_fib)
    
    return fib_sequence


# 生成前20个斐波那契数字
fibonacci_numbers = fibonacci(20)

# 打印结果
print("斐波那契数列的前20个数字:")
for i, num in enumerate(fibonacci_numbers, 1):
    print(f"第{i}个数字: {num}")

print(f"\n完整数列: {fibonacci_numbers}")