import gpxpy
import pandas as pd
import matplotlib.pyplot as plt
import folium
from geopy.distance import geodesic
import os
import webbrowser


class GPXAnalyzer:
    def __init__(self, file_path):
        self.file_path = file_path
        self.gpx = None
        self.track_data = None
        self.total_distance = 0.0

    def load_gpx_file(self):
        """
        Загружает и парсит GPX-файл. Обрабатывает ошибки.
        """
        try:
            with open(self.file_path, 'r') as gpx_file:
                self.gpx = gpxpy.parse(gpx_file)
            if not self.gpx.tracks:
                raise ValueError("GPX-файл не содержит треков.")
        except FileNotFoundError:
            print(f"Файл '{self.file_path}' не найден.")
            exit(1)
        except Exception as e:
            print(f"Ошибка при загрузке GPX-файла: {e}")
            exit(1)

    def extract_track_data(self):
        """
        Извлекает данные из GPX-файла: координаты, высоту, временные метки.
        """
        points = []
        for track in self.gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    points.append({
                        'latitude': point.latitude,
                        'longitude': point.longitude,
                        'elevation': point.elevation,
                        'time': point.time
                    })
        self.track_data = pd.DataFrame(points)
        if self.track_data.empty:
            raise ValueError("GPX-файл не содержит точек.")

    def calculate_metrics(self):
        """
        Рассчитывает метрики: общее расстояние, изменение высоты, скорость.
        """
        # Расчет расстояния между точками
        coords = list(zip(self.track_data['latitude'], self.track_data['longitude']))
        distances = [geodesic(coords[i], coords[i+1]).meters for i in range(len(coords)-1)]
        self.total_distance = sum(distances)

        # Добавление расстояния до каждой точки
        self.track_data['distance'] = [0] + distances
        self.track_data['cumulative_distance'] = self.track_data['distance'].cumsum()

        # Дополнительные метрики
        self.max_elevation = self.track_data['elevation'].max()
        self.min_elevation = self.track_data['elevation'].min()
        self.elevation_gain = max(0, self.track_data['elevation'].diff().fillna(0).clip(lower=0).sum())

    def plot_elevation_profile(self):
        """
        Строит график изменения высоты по маршруту.
        """
        plt.figure(figsize=(10, 6))
        plt.plot(self.track_data['cumulative_distance'], self.track_data['elevation'], color='blue', label='Высота')
        plt.title('Изменение высоты по маршруту')
        plt.xlabel('Расстояние (м)')
        plt.ylabel('Высота (м)')
        plt.legend()
        plt.grid(True)
        plt.show()

    def visualize_track_on_map(self):
        """
        Визуализирует трек на интерактивной карте с использованием folium.
        """
        start_point = (self.track_data.iloc[0]['latitude'], self.track_data.iloc[0]['longitude'])
        m = folium.Map(location=start_point, zoom_start=13)

        # Добавляем линию маршрута
        coordinates = list(zip(self.track_data['latitude'], self.track_data['longitude']))
        folium.PolyLine(locations=coordinates, color='blue', weight=4, opacity=0.7).add_to(m)

        # Добавляем маркеры для начальной и конечной точек
        folium.Marker(
            location=coordinates[0],
            popup="Старт",
            icon=folium.Icon(color='green')
        ).add_to(m)
        folium.Marker(
            location=coordinates[-1],
            popup="Финиш",
            icon=folium.Icon(color='red')
        ).add_to(m)

        # Сохраняем карту в HTML файл
        map_file = "track_map.html"
        m.save(map_file)
        print(f"Карта сохранена в файл '{map_file}'.")
        webbrowser.open(map_file)  # Автоматически открываем карту в браузере

    def run_analysis(self):
        """
        Основной метод для анализа и визуализации данных.
        """
        self.load_gpx_file()
        self.extract_track_data()
        self.calculate_metrics()

        print(f"Общее расстояние маршрута: {self.total_distance:.2f} м")
        print(f"Максимальная высота: {self.max_elevation:.2f} м")
        print(f"Минимальная высота: {self.min_elevation:.2f} м")
        print(f"Набор высоты: {self.elevation_gain:.2f} м")

        self.visualize_track_on_map()
        self.plot_elevation_profile()


if __name__ == "__main__":
    file_path = input("Введите путь к GPX-файлу: ").strip()
    if not os.path.isfile(file_path):
        print("Указанный файл не существует.")
        exit(1)

    analyzer = GPXAnalyzer(file_path)
    analyzer.run_analysis()