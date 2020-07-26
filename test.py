from bs4 import BeautifulSoup

def test():
    sum = 0
    for i in range(10):
        sum += i
    
    return sum

print(test())