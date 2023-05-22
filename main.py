import cv2
from threading import Thread
import time
import math


def draw_arch(frame, point, radius, view_angle, size_of_angle, color, thickness):
    circle_radius = radius
    circle_center_x = point[0]
    circle_center_y = point[1]
    half_of_size_of_angle = size_of_angle / 2
    new_frame = cv2.ellipse(frame,
                            (circle_center_x, circle_center_y),
                            (circle_radius, circle_radius),
                            view_angle - half_of_size_of_angle, 0, size_of_angle, color, thickness)

    diff_x = int(math.cos((view_angle - half_of_size_of_angle) / 180 * math.pi) * circle_radius)
    diff_y = int(math.sin((view_angle - half_of_size_of_angle) / 180 * math.pi) * circle_radius)
    cv2.line(
        new_frame,
        (circle_center_x, circle_center_y),
        (circle_center_x + diff_x, circle_center_y + diff_y),
        color, thickness=thickness, lineType=1
    )
    diff_x = int(math.cos((view_angle + half_of_size_of_angle) / 180 * math.pi) * circle_radius)
    diff_y = int(math.sin((view_angle + half_of_size_of_angle) / 180 * math.pi) * circle_radius)
    cv2.line(
        new_frame,
        (circle_center_x, circle_center_y),
        (circle_center_x + diff_x, circle_center_y + diff_y),
        color, thickness=thickness, lineType=1
    )


class StreamReader:
    def __init__(self, source, maxWidth):
        # store the value
        self.stream = cv2.VideoCapture(source, cv2.CAP_DSHOW)
        self.stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc(*"MJPG"))
        width = self.stream.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = self.stream.get(cv2.CAP_PROP_FRAME_HEIGHT)

        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, maxWidth)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, maxWidth / width * height)

        width = self.stream.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = self.stream.get(cv2.CAP_PROP_FRAME_HEIGHT)

        fps = self.stream.get(cv2.CAP_PROP_FPS)
        fps = fps if fps > 0 else 10

        # if you increase buffer size it helps to consistent frames but if you reduece it it helps to get real time stream
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 3)
        ret, frame = self.stream.read()
        self.fps = fps
        self.real_fps = fps
        self.width = width
        self.height = height
        self.img = frame
        self.frame_id = 1
        thread = Thread(target=self.update, args=([]), daemon=True)
        thread.start()
        print(f"Stream reader started with FPS : {fps} width: {width} height: {height}")

    # override the run function
    def update(self):
        last_fps_calculated_at = time.time()
        frame_id = 0
        while self.stream.isOpened():
            ret, self.img = self.stream.read()
            self.frame_id += 1
            frame_id += 1

            if time.time() - last_fps_calculated_at >= 1:
                fps = frame_id / (time.time() - last_fps_calculated_at)
                if self.frame_id > 1000000:
                    self.frame_id = 0
                frame_id = 1
                last_fps_calculated_at = time.time()
                print(f"Real read FPS: {fps}")


class StreamViewer:
    def __init__(self, streamReader: StreamReader, max_width=None):
        self.streamReader = streamReader

        if max_width == None:
            max_width = streamReader.width
        if max_width > streamReader.width:
            max_width = streamReader.width

        ratio = max_width / streamReader.width
        self.height = int(ratio * streamReader.height)
        self.width = int(max_width)
        thread = Thread(target=self.update, args=([]), daemon=True)
        thread.start()
        print(f"Stream viewer initilized with FPS : {streamReader.fps} width: {self.width} height: {self.height}")

    def postProcess(self, frame, frame_id):

        new_frame = frame
        width = frame.shape[1]
        height = frame.shape[0]

        half_width = int(width / 2)
        half_height = int(height / 2)

        quarter_width = int(width / 4)
        quarter_height = int(height / 4)

        # Draw center lines
        cv2.line(new_frame, (half_width, 0), (half_width, height), (0, 255, 0), thickness=2, lineType=1)
        cv2.line(new_frame, (0, half_height), (width, half_height), (0, 255, 0), thickness=2, lineType=1)

        # draw lines on center lines
        one_height = int(height / 100)
        one_width = int(width / 100)

        grid_counts = 20
        line_width = width / grid_counts
        line_height = height / grid_counts

        for i in range(1, grid_counts):
            cv2.line(
                new_frame,
                (int(i * line_width), int(half_height - one_height)),
                (int(i * line_width), int(half_height + one_height)),
                (0, 255, 0), thickness=1, lineType=1)
            cv2.line(
                new_frame,
                (int(half_width - one_width), int(i * line_height)),
                (int(half_width + one_width), int(i * line_height)),
                (0, 255, 0), thickness=1, lineType=1
            )

        # Draw circle on right top
        circle_radius = int(quarter_height / 2);
        circle_center_x = int(width - circle_radius) - 10
        circle_center_y = circle_radius + 10
        cv2.circle(new_frame, (circle_center_x, circle_center_y), circle_radius,
                   (0, 255, 0), thickness=1, lineType=1)

        view_angle = 180 + frame_id
        size_of_angle = 30

        draw_arch(
            new_frame,
            (circle_center_x, circle_center_y),
            circle_radius,
            view_angle,
            size_of_angle,
            (255, 255, 0),
            3
        )

        # Draw view sight
        circle_radius = int(quarter_height)
        circle_center_x = int(width - circle_radius ) - 10
        circle_center_y = (quarter_height + 10) * 2


        view_angle = 360 - 45
        size_of_angle = 90
        draw_arch(
            new_frame,
            (circle_center_x, circle_center_y),
            circle_radius,
            view_angle,
            size_of_angle,
            (0, 255, 0),
            1
        )
        view_angle = (280 + frame_id % 70)
        size_of_angle = 20
        draw_arch(
            new_frame,
            (circle_center_x, circle_center_y),
            circle_radius,
            view_angle,
            size_of_angle,
            (255, 255, 0),
            3
        )

        return new_frame

    def update(self):
        captured_framed = 0
        last_frame_id = 0
        last_fps_calculated_at = time.time()
        while True:

            # Capture the video frame
            # by frame

            while last_frame_id == self.streamReader.frame_id:
                time.sleep(0.5 / stream_reader.fps)

            frame = self.postProcess(self.streamReader.img, self.streamReader.frame_id)
            last_frame_id = self.streamReader.frame_id

            # Display the resulting frame
            cv2.imshow('frame', cv2.resize(frame, (self.width, self.height)))

            captured_framed += 1

            if time.time() - last_fps_calculated_at >= 1:
                fps = captured_framed / (time.time() - last_fps_calculated_at)
                captured_framed = 0
                last_fps_calculated_at = time.time()
                print(f"Show read FPS: {fps}")

            time.sleep(0.5 / stream_reader.fps)
            # quitting button you may use any
            # desired button of your choice
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Destroy all the windows
        cv2.destroyAllWindows()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    stream_reader = StreamReader(0, 1920)
    stream_viewer = StreamViewer(stream_reader, 1920)

    while True:
        time.sleep(5)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
