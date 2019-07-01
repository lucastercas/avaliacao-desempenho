import matplotlib.pyplot as plt

plt.style.use('ggplot')
def plot_each(title,ylabel, yvalues, xlabel, xvalues, fileName):
    print(f"Ploting {title} to file {fileName}")
    plt.title(title)
    plt.plot(xvalues, yvalues)
    plt.ylabel(ylabel)
    plt.xlabel(xlabel)
    plt.savefig(f'graphics/{fileName}')
    plt.clf()

def plot_all(title, ylabel, yvalues, xlabel, xvalues, fileName, legend):
    print(f"Ploting {title} to file {fileName}")
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xlabel(xlabel)
    for i in range(len(yvalues)):
        plt.plot(xvalues, yvalues[i], label=legend[i])
    plt.legend()
    plt.savefig(f'graphics/{fileName}')
    plt.clf()

