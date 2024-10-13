from nicegui import ui
import threading
import time
import matplotlib.pyplot as plt
import io
import base64

class TestCase:
    def __init__(self, case_id, images):
        self.case_id = case_id
        self.images = images  # List of image filenames

    def __repr__(self):
        return f"TestCase(case_id={self.case_id}, images={self.images})"

    def display(self):
        raise NotImplementedError("Subclasses should implement this!")

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
        ui.label(f"TestCase ID: {self.case_id}")
        ui.label(f"Images: {', '.join(self.images)}")
        self.label = ui.label(f"Countdown: {self.remaining} seconds")
        self.elapsed_label = ui.label("")  # Label to display elapsed time
        start_stop_button = ui.button('Start/Stop Countdown', on_click=self.toggle_countdown)

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
            with ui.row():
                ui.label('Number of Test Cases:')
                self.slider_label = ui.label(f'{self.testcase_cnt}')
                ui.slider(min=1, max=10, value=self.testcase_cnt, on_change=self.update_testcase_cnt)

            for test_suite in self.test_suites:
                ui.button(test_suite.name, on_click=lambda ts=test_suite: self.start_test_suite(ts))

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
            ui.label('Introduction Page')
            ui.button('Next', on_click=lambda: self.show_test_case_pages(test_cases, 0))
            ui.button('Back', on_click=lambda: ui.navigate.to('/'))

    def show_test_case_pages(self, test_cases, index):
        if index < len(test_cases):
            @ui.page(f'/test_case_{index}')
            def test_case_page():
                test_cases[index].reset_countdown()  # Reset countdown before displaying
                test_cases[index].display()
                ui.button('Next', on_click=lambda: self.show_test_case_pages(test_cases, index + 1))
                ui.button('Back', on_click=lambda: ui.navigate.to('/'))
            ui.navigate.to(f'/test_case_{index}')
        else:
            self.show_summary_page()
            ui.navigate.to('/summary')

    def record_time(self, test_case):
        if test_case.elapsed_time is not None:
            self.temp_table.append({
                'case_id': test_case.case_id,
                'elapsed_time': test_case.elapsed_time,
                'alert_time': test_case.alert_time
            })
            print(f"Recorded time for case {test_case.case_id}: {test_case.elapsed_time:.2f} seconds")

    def show_summary_page(self):
        @ui.page('/summary')
        def summary_page():
            ui.label('Summary Page')
            if self.temp_table:
                case_ids = [f"Case {record['case_id']}" for record in self.temp_table]
                elapsed_times = [record['elapsed_time'] for record in self.temp_table]
                alert_times = [record['alert_time'] for record in self.temp_table]

                # Determine bar colors based on alert_time
                colors = ['red' if elapsed > alert else 'blue' for elapsed, alert in zip(elapsed_times, alert_times)]

                # Create a bar chart
                plt.figure(figsize=(8, 4), dpi=100)  # Increase DPI for better resolution
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

            ui.button('Back', on_click=lambda: ui.navigate.to('/'))

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

    # Run the app
    app.run()