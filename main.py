from abc import ABC, abstractmethod
from nicegui import ui
import threading
import time
import matplotlib.pyplot as plt
import io
import base64

class TestCase(ABC):
    def __init__(self, case_id, images):
        self.case_id = case_id
        self.images = images  # List of image filenames

    def __repr__(self):
        return f"TestCase(case_id={self.case_id}, images={self.images})"

    @abstractmethod
    def display(self):
        pass

    @staticmethod
    @abstractmethod
    def intro_display():
        pass

    @staticmethod
    @abstractmethod
    def summary_display(temp_table):
        pass

class SingleCountdownTestCase(TestCase):
    def __init__(self, case_id, images, countdown, alert_time):
        super().__init__(case_id, images)
        self.countdown = countdown
        self.initial_countdown = countdown
        self.remaining = countdown
        self.alert_time = alert_time
        self.label = None
        self.elapsed_label = None
        self.stop_event = threading.Event()  # Event to control the countdown thread
        self.start_time = None
        self.elapsed_time = None
        self.started = False  # Flag to indicate if the countdown has started
        self.stopped = False  # Flag to indicate if the countdown has stopped

    def __repr__(self):
        return f"SingleCountdownTestCase(case_id={self.case_id}, images={self.images}, countdown={self.countdown}, alert_time={self.alert_time})"

    def display(self):
        with ui.column().classes('items-center justify-center').style('height: 100vh; width: 100vw'):
            ui.label(f"TestCase ID: {self.case_id}")
            ui.label(f"Images: {', '.join(self.images)}")
            self.label = ui.label(f"Countdown: {self.remaining} seconds")
            self.elapsed_label = ui.label("")  # Label to display elapsed time
            start_stop_button = ui.button('Start/Stop Countdown', on_click=self.toggle_countdown).classes('q-pa-md q-ma-md')

            # Add a keyboard event listener for the spacebar
            def on_key(event):
                if event.key == ' ':
                    self.toggle_countdown()

            ui.on('keydown', on_key)

            # Set focus to the Start/Stop button to ensure key events are captured
            ui.run_javascript(f'document.getElementById("{start_stop_button.id}").focus();')

    def toggle_countdown(self):
        if not self.started and not self.stopped:
            self.start_countdown()
        elif self.started and not self.stopped:
            self.stop_countdown()

    def start_countdown(self):
        self.stop_event.clear()  # Clear the event for the new countdown
        self.start_time = time.time()
        self.started = True

        def countdown():
            while not self.stop_event.is_set():
                time.sleep(1)
                self.remaining -= 1
                self.label.set_text(f"Countdown: {self.remaining} seconds")

        threading.Thread(target=countdown).start()

    def stop_countdown(self):
        self.stop_event.set()  # Stop the countdown
        self.elapsed_time = time.time() - self.start_time
        self.elapsed_label.set_text(f"Elapsed time: {self.elapsed_time:.2f} seconds")
        self.started = False
        self.stopped = True  # Mark as stopped
        # Record the time in the temporary table
        app.record_time(self)

    def reset_countdown(self):
        self.stop_event.set()  # Stop any existing countdown
        self.remaining = self.initial_countdown
        self.started = False
        self.stopped = False  # Reset stopped flag
        if self.label:
            self.label.set_text(f"Countdown: {self.remaining} seconds")
        if self.elapsed_label:
            self.elapsed_label.set_text("")

    @staticmethod
    def intro_display():
        with ui.column().classes('items-center justify-center').style('height: 100vh; width: 100vw'):
            ui.label('Introduction Page for Single Countdown Test Case')
            ui.button('Next', on_click=lambda: ui.navigate.to('/test_case_0')).classes('q-pa-md q-ma-md')
            ui.button('Back', on_click=lambda: ui.navigate.to('/')).classes('q-pa-md q-ma-md')

    @staticmethod
    def summary_display(temp_table):
        with ui.column().classes('items-center justify-center').style('height: 100vh; width: 100vw'):
            ui.label('Summary Page for Single Countdown Test Case')
            if temp_table:
                case_ids = [f"Case {record['case_id']}" for record in temp_table]
                elapsed_times = [record['elapsed_time'] for record in temp_table]
                alert_times = [record['alert_time'] for record in temp_table]

                # Determine bar colors based on alert_time
                colors = ['red' if elapsed > alert else 'blue' for elapsed, alert in zip(elapsed_times, alert_times)]

                # Create a bar chart
                plt.figure(figsize=(8, 4), dpi=200)  # Increase DPI for better resolution
                bars = plt.bar(case_ids, elapsed_times, color=colors)
                plt.xlabel('Case ID')
                plt.ylabel('Elapsed Time (seconds)')
                plt.title('Elapsed Time for Each Test Case')

                # Add a horizontal line for the average time
                avg_time = sum(elapsed_times) / len(elapsed_times)
                plt.axhline(y=avg_time, color='green', linestyle='--')
                plt.text(len(case_ids) - 1, avg_time + 0.5, f'Avg: {avg_time:.2f}s', color='green', va='bottom')

                # Save the plot to a PNG image in memory
                buf = io.BytesIO()
                plt.savefig(buf, format='png')
                buf.seek(0)
                img_base64 = base64.b64encode(buf.read()).decode('utf-8')
                buf.close()

                # Set default properties for the image
                ui.image.default_props(add='width=800px height=400px')
                ui.image(f'data:image/png;base64,{img_base64}')

            ui.button('Back', on_click=lambda: ui.navigate.to('/')).classes('q-pa-md q-ma-md')

class TripleCountdownTestCase(TestCase):
    def __init__(self, case_id, images, countdown=60, alert_times=[60,18,21,21]):
        super().__init__(case_id, images)
        self.countdown = countdown
        self.initial_countdown = countdown
        self.remaining = countdown
        self.alert_times = alert_times  # List of alert times [att, at1, at2, at3]
        self.label = None
        self.elapsed_label = None
        self.stop_event = threading.Event()  # Event to control the countdown thread
        self.start_time = None
        self.elapsed_time = None
        self.times = []  # List to store times [t1, t2, t3]
        self.started = False  # Flag to indicate if the countdown has started
        self.stopped = False  # Flag to indicate if the countdown has stopped
        self.toggle_count = 0  # Count the number of times Start/Stop is pressed

    def __repr__(self):
        return f"TripleCountdownTestCase(case_id={self.case_id}, images={self.images}, countdown={self.countdown}, alert_times={self.alert_times})"

    def display(self):
        with ui.column().classes('items-center justify-center').style('height: 100vh; width: 100vw'):
            ui.label(f"TestCase ID: {self.case_id}")
            ui.label(f"Images: {', '.join(self.images)}")
            self.label = ui.label(f"Countdown: {self.remaining} seconds")
            self.elapsed_label = ui.label("")  # Label to display elapsed time
            start_stop_button = ui.button('Start/Stop Countdown', on_click=self.toggle_countdown).classes('q-pa-md q-ma-md')

            # Add a keyboard event listener for the spacebar
            def on_key(event):
                if event.key == ' ':
                    self.toggle_countdown()

            ui.on('keydown', on_key)

            # Set focus to the Start/Stop button to ensure key events are captured
            ui.run_javascript(f'document.getElementById("{start_stop_button.id}").focus();')

    def toggle_countdown(self):
        if not self.started and not self.stopped:
            self.start_countdown()
        elif self.started and not self.stopped:
            self.toggle_count += 1
            self.times.append(time.time() - self.start_time)
            if self.toggle_count == 3:
                self.stop_countdown()

    def start_countdown(self):
        self.stop_event.clear()  # Clear the event for the new countdown
        self.start_time = time.time()
        self.started = True

        def countdown():
            while not self.stop_event.is_set():
                time.sleep(1)
                self.remaining -= 1
                self.label.set_text(f"Countdown: {self.remaining} seconds")

        threading.Thread(target=countdown).start()

    def stop_countdown(self):
        self.stop_event.set()  # Stop the countdown
        self.elapsed_time = time.time() - self.start_time
        #self.times.append(self.elapsed_time)
        self.elapsed_label.set_text(f"Elapsed time: {self.elapsed_time:.2f} seconds")
        self.started = False
        self.stopped = True  # Mark as stopped
        # Record the time in the temporary table
        app.record_time(self)

    def reset_countdown(self):
        self.stop_event.set()  # Stop any existing countdown
        self.remaining = self.initial_countdown
        self.started = False
        self.stopped = False  # Reset stopped flag
        self.toggle_count = 0
        self.times = []
        if self.label:
            self.label.set_text(f"Countdown: {self.remaining} seconds")
        if self.elapsed_label:
            self.elapsed_label.set_text("")

    @staticmethod
    def intro_display():
        with ui.column().classes('items-center justify-center').style('height: 100vh; width: 100vw'):
            ui.label('Introduction Page for Triple Countdown Test Case')
            ui.button('Next', on_click=lambda: ui.navigate.to('/test_case_0')).classes('q-pa-md q-ma-md')
            ui.button('Back', on_click=lambda: ui.navigate.to('/')).classes('q-pa-md q-ma-md')

    @staticmethod
    def summary_display(temp_table):
        with ui.column().classes('items-center justify-center').style('height: 100vh; width: 100vw'):
            ui.label('Summary Page for Triple Countdown Test Case')
            if temp_table:
                case_ids = [f"Case {record['case_id']}" for record in temp_table]
                total_times = [record['elapsed_time'] for record in temp_table]
                times = [record['times'] for record in temp_table]
                alert_times = [record['alert_times'] for record in temp_table]

                # Create a bar chart
                plt.figure(figsize=(8, 4), dpi=200)  # Increase DPI for better resolution
                for i, case_id in enumerate(case_ids):
                    t1, t2, t3 = times[i]
                    att, at1, at2, at3 = alert_times[i]
                    total_time = total_times[i]

                    # Function to shift color towards red
                    def shift_towards_red(color, factor=0.5):
                        r, g, b = color
                        r = min(1.0, r + factor * (1.0 - r))
                        g = max(0.0, g - factor * g)
                        b = max(0.0, b - factor * b)
                        return (r, g, b)

                    # Original colors
                    color_t1 = (0.0, 0.0, 0.5)  # darkblue
                    # darkyellow for t2
                    color_t2 = (0.5, 0.5, 0.0)  # darkyellow
                    color_t3 = (0.58, 0.0, 0.83)  # darkviolet

                    # Adjust colors based on alert times
                    if t1 > at1:
                        color_t1 = shift_towards_red(color_t1)
                    if t2 > at2:
                        color_t2 = shift_towards_red(color_t2)
                    if t3 > at3:
                        color_t3 = shift_towards_red(color_t3)
                    edgecolor = 'red' if total_time > att else 'black'

                    plt.bar(case_id, t1, color=color_t1, alpha=0.6, edgecolor=edgecolor)
                    plt.bar(case_id, t2, bottom=t1, color=color_t2, alpha=0.6, edgecolor=edgecolor)
                    plt.bar(case_id, t3, bottom=t1 + t2, color=color_t3, alpha=0.6, edgecolor=edgecolor)

                plt.xlabel('Case ID')
                plt.ylabel('Time (seconds)')
                plt.title('Time Breakdown for Each Test Case')

                # Save the plot to a PNG image in memory
                buf = io.BytesIO()
                plt.savefig(buf, format='png')
                buf.seek(0)
                img_base64 = base64.b64encode(buf.read()).decode('utf-8')
                buf.close()

                # Set default properties for the image
                ui.image.default_props(add='width=800px height=400px')
                ui.image(f'data:image/png;base64,{img_base64}')

            ui.button('Back', on_click=lambda: ui.navigate.to('/')).classes('q-pa-md q-ma-md')

class TestSuite:
    def __init__(self, name):
        self.name = name
        self.test_cases = []

    def add_test_case(self, test_case):
        self.test_cases.append(test_case)

    def __repr__(self):
        return f"TestSuite(name={self.name}, test_cases={self.test_cases})"

class App:
    def __init__(self):
        self.test_suites = []
        self.testcase_cnt = 1
        self.temp_table = []

    def add_test_suite(self, test_suite):
        self.test_suites.append(test_suite)

    def run(self):
        @ui.page('/')
        def main_page():
            with ui.column().classes('items-center justify-center').style('height: 100vh; width: 100vw'):
                with ui.row().classes('items-center'):
                    ui.label('Number of Test Cases:')
                    self.slider_label = ui.label(f'{self.testcase_cnt}')
                    ui.slider(min=1, max=10, value=self.testcase_cnt, on_change=self.update_testcase_cnt)

                for test_suite in self.test_suites:
                    ui.button(test_suite.name, on_click=lambda ts=test_suite: self.start_test_suite(ts)).classes('q-pa-md q-ma-md')

        ui.run()

    def update_testcase_cnt(self, event):
        self.testcase_cnt = event.value
        self.slider_label.set_text(f'{self.testcase_cnt}')
        print(f"Updated testcase_cnt to: {self.testcase_cnt}")

    def start_test_suite(self, test_suite):
        print(f"Starting test suite with {self.testcase_cnt} test cases.")
        self.temp_table = []  # Reset the temporary table
        selected_cases = test_suite.test_cases[:self.testcase_cnt]
        self.show_intro_page(selected_cases)
        ui.navigate.to('/intro')

    def show_intro_page(self, test_cases):
        @ui.page('/intro')
        def intro_page():
            test_cases[0].intro_display()

        # Predefine all test case pages
        for index in range(len(test_cases)):
            self.define_test_case_page(test_cases, index)

    def define_test_case_page(self, test_cases, index):
        @ui.page(f'/test_case_{index}')
        def test_case_page():
            with ui.column().classes('items-center justify-center').style('height: 100vh; width: 100vw'):
                test_cases[index].reset_countdown()  # Reset countdown before displaying
                test_cases[index].display()
                ui.button('Next', on_click=lambda: self.show_test_case_pages(test_cases, index + 1)).classes('q-pa-md q-ma-md')
                ui.button('Back', on_click=lambda: ui.navigate.to('/')).classes('q-pa-md q-ma-md')

    def show_test_case_pages(self, test_cases, index):
        if index < len(test_cases):
            ui.navigate.to(f'/test_case_{index}')
        else:
            self.show_summary_page()
            ui.navigate.to('/summary')

    def record_time(self, test_case):
        if isinstance(test_case, TripleCountdownTestCase):
            self.temp_table.append({
                'case_id': test_case.case_id,
                'elapsed_time': test_case.elapsed_time,
                'times': test_case.times,
                'alert_times': test_case.alert_times,
                'case': test_case  # Store the test_case object itself
            })
        else:
            self.temp_table.append({
                'case_id': test_case.case_id,
                'elapsed_time': test_case.elapsed_time,
                'alert_time': test_case.alert_time,
                'case': test_case  # Store the test_case object itself
            })
        print(f"Recorded time for case {test_case.case_id}: {test_case.elapsed_time:.2f} seconds")

    def show_summary_page(self):
        @ui.page('/summary')
        def summary_page():
            if self.temp_table:
                self.temp_table[0]['case'].summary_display(self.temp_table)

# Example usage
if __name__ in {"__main__", "__mp_main__"}:
    app = App()

    # Create some test cases
    test_case1 = SingleCountdownTestCase(case_id=1, images=["assets/image1.png", "assets/image2.png"], countdown=30, alert_time=5)
    test_case2 = SingleCountdownTestCase(case_id=2, images=["assets/image3.png"], countdown=45, alert_time=5)
    test_case3 = SingleCountdownTestCase(case_id=3, images=["assets/image4.png"], countdown=60, alert_time=5)
    test_case4 = SingleCountdownTestCase(case_id=4, images=["assets/image5.png"], countdown=75, alert_time=5)
    test_case5 = SingleCountdownTestCase(case_id=5, images=["assets/image6.png"], countdown=90, alert_time=5)

    # Create a test suite and add test cases to it
    test_suite = TestSuite(name="Sample Quiz")
    test_suite.add_test_case(test_case1)
    test_suite.add_test_case(test_case2)
    test_suite.add_test_case(test_case3)
    test_suite.add_test_case(test_case4)
    test_suite.add_test_case(test_case5)

    # Add test suite to app
    app.add_test_suite(test_suite)

    # Create a TripleCountdownTestCase and add it to a new test suite
    triple_test_case = TripleCountdownTestCase(case_id=6, images=["assets/image7.png"], countdown=120, alert_times=[100, 3, 3, 4])
    triple_test_suite = TestSuite(name="Triple Countdown Test")
    triple_test_suite.add_test_case(triple_test_case)

    # Add the new test suite to app
    app.add_test_suite(triple_test_suite)

    # Run the app
    app.run()