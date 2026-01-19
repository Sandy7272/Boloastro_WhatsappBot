import matplotlib.pyplot as plt
import matplotlib.image as mpimg

# PUT YOUR REFERENCE IMAGE PATH HERE
image_path = "assets/cover.png" 

def onclick(event):
    if event.xdata is not None and event.ydata is not None:
        print(f"📍 Coordinates: x={int(event.xdata)}, y={int(event.ydata)}")

img = mpimg.imread(image_path)
fig, ax = plt.subplots()
ax.imshow(img)
cid = fig.canvas.mpl_connect('button_press_event', onclick)
plt.title("Click on where you want text to start!")
plt.show()