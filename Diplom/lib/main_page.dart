import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'dart:async';

class MainPage extends StatefulWidget {
  final String username;

  const MainPage({super.key, required this.username});

  @override
  State<MainPage> createState() => _MainPageState();
}

class _MainPageState extends State<MainPage> {
  List<LatLng> points = [];
  List<dynamic> searchResults = [];

  TextEditingController searchController = TextEditingController();
  MapController mapController = MapController();
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
          /// 🔍 Поиск
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: searchController,
                    onChanged: searchSuggestions,
                    decoration: const InputDecoration(
                      hintText: "Введите место (например Riga)",
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.search),
                  onPressed: searchLocation,
                ),
              ],
            ),
          ),

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

          /// 🗺 Карта
          Expanded(
            child: Center(
              child: Container(
                width: 800,
                height: 500,
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(12),
                  child: FlutterMap(
                    mapController: mapController,
                    options: MapOptions(
                      initialCenter: LatLng(56.95, 24.10),
                      initialZoom: 10,
                      onTap: (_, pos) => addPoint(pos),
                    ),
                    children: [
                      TileLayer(
                        urlTemplate:
                            'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                        userAgentPackageName: 'com.example.myapp',
                      ),
                      MarkerLayer(
                        markers: points.map((p) {
                          return Marker(
                            point: p,
                            width: 40,
                            height: 40,
                            child: const Icon(
                              Icons.location_pin,
                              color: Colors.red,
                            ),
                          );
                        }).toList(),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
