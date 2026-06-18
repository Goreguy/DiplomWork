//главная рабочая страница
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'dart:async';
import 'analysis_result_page.dart';

import '../SearchAndMapWidgets/search_bar.dart';
import '../SearchAndMapWidgets/map_widget.dart';

class MainPage extends StatefulWidget {
  final String username;

  const MainPage({super.key, required this.username});

  @override
  State<MainPage> createState() => _MainPageState();
}

class _MainPageState extends State<MainPage> {
  String? heatmapUrl;
  List<dynamic> ndviHistory = [];
  double? meanNdvi;
  String? vegetationStatus;
  String? rgbUrl;

  // Результаты CNN-модуля машинного обучения
  String? cnnImageUrl;
  double? cnnMeanNdvi;
  String? cnnStatus;
  double? cnnMse;
  double? cnnMae;
  double? cnnR2;
  String? cnnField;
  String? cnnDatePrefix;
  String? cnnError;

  List<LatLng> points = [];
  List<dynamic> searchResults = [];

  final TextEditingController searchController = TextEditingController();
  final MapController mapController = MapController();
  Timer? _debounce;

  // получение истории
  Future<void> loadHistory() async {
    final url = Uri.parse('http://127.0.0.1:8000/history');

    final body = {
      "points": points.map((p) {
        return {"lat": p.latitude, "lon": p.longitude};
      }).toList(),
    };

    try {
      final response = await http.post(
        url,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode(body),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);

        setState(() {
          ndviHistory = data["history"];
        });
      }
    } catch (e) {
      debugPrint("Ошибка history: $e");
    }
  }

  // добавление точки
  void addPoint(LatLng point) {
    /// максимум 4 точки
    if (points.length >= 4) return;

    /// проверка расстояния
    if (points.isNotEmpty) {
      final Distance distance = Distance();

      double meters = distance(points.last, point);

      /// максимум 3 км
      if (meters > 3000) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Точка слишком далеко (максимум 3 км)")),
        );

        return;
      }
    }

    setState(() {
      points.add(point);
    });
  }

  // поиск подсказок
  Future<void> searchSuggestions(String query) async {
    if (_debounce?.isActive ?? false) _debounce!.cancel();

    _debounce = Timer(const Duration(milliseconds: 1500), () async {
      if (query.isEmpty || query.length < 3) {
        setState(() => searchResults = []);
        return;
      }

      try {
        final url = Uri.parse('https://photon.komoot.io/api/?q=$query&limit=5');

        final response = await http
            .get(url, headers: {'User-Agent': 'FlutterApp'})
            .timeout(const Duration(seconds: 5));

        if (response.statusCode == 200) {
          final data = jsonDecode(response.body);

          setState(() {
            searchResults = data['features'];
          });
        }
      } catch (e) {
        debugPrint("Ошибка поиска: $e");
      }
    });
  }

  //Поиск по карте
  Future<void> searchLocation() async {
    String query = searchController.text.trim();

    if (query.isEmpty) return;

    try {
      final url = Uri.parse('https://photon.komoot.io/api/?q=$query&limit=5');

      final response = await http.get(
        url,
        headers: {'User-Agent': 'FlutterApp'},
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);

        final features = data['features'];

        if (features.isNotEmpty) {
          final lon = features[0]['geometry']['coordinates'][0];

          final lat = features[0]['geometry']['coordinates'][1];

          mapController.move(LatLng(lat, lon), 13);
        } else {
          debugPrint("Ничего не найдено");
        }
      } else {
        debugPrint("Ошибка HTTP: ${response.statusCode}");
      }
    } catch (e) {
      debugPrint("Ошибка: $e");
    }
  }

  // загрузка heatmap
  Future<void> loadHeatmap() async {
    final url = Uri.parse('http://127.0.0.1:8000/heatmap');

    final body = {
      "points": points.map((p) {
        return {"lat": p.latitude, "lon": p.longitude};
      }).toList(),
    };

    final response = await http.post(
      url,
      headers: {"Content-Type": "application/json"},
      body: jsonEncode(body),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);

      heatmapUrl =
          "${data["image_url"]}?t=${DateTime.now().millisecondsSinceEpoch}";
    }
  }

  Future<void> loadRgb() async {
    final url = Uri.parse('http://127.0.0.1:8000/rgb');

    final body = {
      "points": points.map((p) {
        return {"lat": p.latitude, "lon": p.longitude};
      }).toList(),
    };

    try {
      final response = await http.post(
        url,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode(body),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);

        setState(() {
          rgbUrl =
              "${data["image_url"]}?t=${DateTime.now().millisecondsSinceEpoch}";
        });
      }
    } catch (e) {
      debugPrint("Ошибка загрузки RGB: $e");
    }
  }

  // загрузка результата CNN-модуля
  Future<void> loadCnnPrediction() async {
    final url = Uri.parse('http://127.0.0.1:8000/ml/predict-current');

    final body = {
      "points": points.map((p) {
        return {"lat": p.latitude, "lon": p.longitude};
      }).toList(),
    };

    try {
      final response = await http.post(
        url,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode(body),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);

        setState(() {
          cnnImageUrl =
              "${data["image_url"]}?t=${DateTime.now().millisecondsSinceEpoch}";
          cnnMeanNdvi = (data["mean_predicted_ndvi"] as num?)?.toDouble();
          cnnStatus = data["status"]?.toString();
          cnnMse = (data["mse"] as num?)?.toDouble();
          cnnMae = (data["mae"] as num?)?.toDouble();
          cnnR2 = (data["r2"] as num?)?.toDouble();
          cnnField = data["field"]?.toString();
          cnnDatePrefix = data["date_prefix"]?.toString();
          cnnError = null;
        });
      } else {
        final data = jsonDecode(response.body);
        setState(() {
          cnnError =
              data["detail"]?.toString() ?? "CNN-модуль временно недоступен";
        });
      }
    } catch (e) {
      setState(() {
        cnnError = "Ошибка CNN-модуля: $e";
      });

      debugPrint("Ошибка CNN: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text("Пользователь: ${widget.username}"),
        backgroundColor: Colors.green,
      ),

      body: Column(
        children: [
          //Виджет поиска
          SearchBarWidget(
            controller: searchController,
            onChanged: searchSuggestions,
            onSearch: searchLocation,
          ),

          //Подсказки
          if (searchResults.isNotEmpty)
            Container(
              height: 200,
              color: Colors.white,
              child: ListView.builder(
                itemCount: searchResults.length,
                itemBuilder: (context, index) {
                  final item = searchResults[index];

                  return ListTile(
                    title: Text(item['properties']['name']),
                    onTap: () {
                      final lat = item['geometry']['coordinates'][1];
                      final lon = item['geometry']['coordinates'][0];

                      mapController.move(LatLng(lat, lon), 13);

                      setState(() {
                        searchResults = [];
                        searchController.text = item['properties']['name'];
                      });
                    },
                  );
                },
              ),
            ),

          //Карта
          MapWidget(
            mapController: mapController,
            points: points,
            onTap: addPoint,
          ),

          //Очистить полигоны
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              ElevatedButton(
                onPressed: () {
                  setState(() {
                    points.clear();
                  });
                },
                child: const Text("Очистить"),
              ),

              const SizedBox(width: 20),

              ElevatedButton(
                onPressed: analyzePolygon,
                child: const Text("Анализ"),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // анализ полигона
  Future<void> analyzePolygon() async {
    setState(() {
      meanNdvi = null;
      vegetationStatus = null;
      heatmapUrl = null;
      rgbUrl = null;
      cnnImageUrl = null;
      cnnMeanNdvi = null;
      cnnStatus = null;
      cnnMse = null;
      cnnMae = null;
      cnnR2 = null;
      cnnField = null;
      cnnDatePrefix = null;
      cnnError = null;
      ndviHistory.clear();
    });

    if (points.length < 4) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text("Выберите 4 точки")));

      return;
    }

    final url = Uri.parse('http://127.0.0.1:8000/analyze');

    final body = {
      "points": points.map((p) {
        return {"lat": p.latitude, "lon": p.longitude};
      }).toList(),
    };

    try {
      final response = await http.post(
        url,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode(body),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);

        setState(() {
          meanNdvi = data["mean_ndvi"];
          vegetationStatus = data["status"];
        });

        await loadHistory();
        await loadHeatmap();
        await loadRgb();
        await loadCnnPrediction();

        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => AnalysisResultPage(
              meanNdvi: meanNdvi!,
              vegetationStatus: vegetationStatus!,
              history: ndviHistory,
              heatmapUrl: heatmapUrl,
              rgbUrl: rgbUrl,
              cnnImageUrl: cnnImageUrl,
              cnnMeanNdvi: cnnMeanNdvi,
              cnnStatus: cnnStatus,
              cnnMse: cnnMse,
              cnnMae: cnnMae,
              cnnR2: cnnR2,
              cnnField: cnnField,
              cnnDatePrefix: cnnDatePrefix,
              cnnError: cnnError,
            ),
          ),
        );
      } else {
        debugPrint("Ошибка сервера: ${response.statusCode}");
      }
    } catch (e) {
      debugPrint("Ошибка: $e");
    }
  }
}
