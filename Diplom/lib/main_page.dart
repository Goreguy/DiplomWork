import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'dart:async';

import 'SearchAndMapWidgets/search_bar.dart';
import 'SearchAndMapWidgets/map_widget.dart';

class MainPage extends StatefulWidget {
  final String username;

  const MainPage({super.key, required this.username});

  @override
  State<MainPage> createState() => _MainPageState();
}

class _MainPageState extends State<MainPage> {
  List<LatLng> points = [];
  List<dynamic> searchResults = [];

  final TextEditingController searchController = TextEditingController();
  final MapController mapController = MapController();
  Timer? _debounce;

  // добавление точки
  void addPoint(LatLng point) {
    setState(() {
      if (points.length < 4) {
        points.add(point);
      }
    });
  }

  // поиск подсказок
  Future<void> searchSuggestions(String query) async {
    if (_debounce?.isActive ?? false) _debounce!.cancel();

    _debounce = Timer(const Duration(milliseconds: 500), () async {
      if (query.isEmpty) {
        setState(() => searchResults = []);
        return;
      }

      try {
        final url = Uri.parse(
          'https://nominatim.openstreetmap.org/search?q=$query&format=json&limit=1',
        );

        final response = await http.get(
          url,
          headers: {'User-Agent': 'FlutterApp'},
        );

        if (response.statusCode == 200) {
          final data = jsonDecode(response.body);

          setState(() {
            searchResults = data;
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
      final url = Uri.parse(
        'https://nominatim.openstreetmap.org/search?q=$query&format=json&limit=1',
      );

      final response = await http.get(
        url,
        headers: {'User-Agent': 'FlutterApp'},
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);

        if (data.isNotEmpty) {
          final lat = double.parse(data[0]['lat']);
          final lon = double.parse(data[0]['lon']);

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
                    title: Text(item['display_name']),
                    onTap: () {
                      final lat = double.parse(item['lat']);
                      final lon = double.parse(item['lon']);

                      mapController.move(LatLng(lat, lon), 13);

                      setState(() {
                        searchResults = [];
                        searchController.text = item['display_name'];
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
                onPressed: () {
                  if (points.length < 4) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text("Выберите 4 точки")),
                    );
                    return;
                  }

                  /// реализовать отправку в пайтон
                  debugPrint("Координаты полигона:");
                  for (var p in points) {
                    debugPrint("${p.latitude}, ${p.longitude}");
                  }
                },
                child: const Text("Анализ"),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
