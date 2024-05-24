import numpy as np

def calculateplot(win:list, easy:list, types:str, deg:int):
    print(f"[Approximation type {types}]")
    print(win)
    print(easy)
    x = np.array(win)
    y = np.array(easy)

    coeff = np.polyfit(x, y, deg)
    print(f"Polynomial Coefficient: {coeff}")

    # Function to approximate easyh based on winh values
    def approximate_easyh(winh_value):
        return np.polyval(coeff, winh_value)

    # Example usage: Approximate easyh for a winh value of 50
    predicted_easyh = approximate_easyh(325)
    # easypredicted_easyhpred = list(predicted_easyh)
    # predicted_easyh = [int(val) for val in predicted_easyh]
    print(f"Input value: {x}")
    print(f"Result target: {y}")
    print(f"Predicted easy from win: {predicted_easyh}")

    p = np.poly1d(coeff)

    import matplotlib.pyplot as plt
    if types == "h":
        xaxis = np.arange(100)
    else:
        xaxis = np.arange(2000)
    yaxis = p(xaxis)
    plt.figure()
    plt.plot(xaxis, yaxis)
    if types == "h":
        plt.ylim(-10,100)
    else:
        plt.ylim(100,2000)
    plt.xlabel("X-axis")
    plt.ylabel("Y-axis")
    plt.title("Polynomial Plot (poly1d)")
    plt.grid(True)
    plt.show()

if __name__=="__main__":
    winocrbox = [(21, 357, 287, 235), (28, 462, 287, 293), (56, 537, 287, 360), (43, 710, 287, 436), (49, 814, 287, 525), (61, 1013, 287, 626), (79, 1315, 287, 746)]
    easyocrbox = [(26, 364, 284, 230), (33, 466, 284, 287), (40, 552, 285, 355), (54, 732, 282, 426), (60, 834, 283, 515), (73, 1046, 282, 615), (88, 1356, 283, 735)]
    winh = [box[0] for box in winocrbox]
    winw = [box[1] for box in winocrbox]
    easyh = [box[0] for box in easyocrbox]
    easyw = [box[1] for box in easyocrbox]
    # calculateplot(winh, easyh,"h",5)
    # print("\n")
    calculateplot(winw, easyw,"w",2)