import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:geocoding/geocoding.dart';

class MainPage extends StatefulWidget {
  final String username;

  const MainPage({super.key, required this.username});

  @override
  State<MainPage> createState() => _MainPageState();
}

class _MainPageState extends State<MainPage> {
  final List<LatLng> points = [];

  TextEditingController searchController = TextEditingController();
  MapController mapController = MapController();

  //Поиск по карте
  Future<void> searchLocation() async {
    String query = searchController.text;

    if (query.isEmpty) return;

    List<Location> locations = await locationFromAddress(query);

    if (locations.isNotEmpty) {
      final loc = locations.first;

      mapController.move(LatLng(loc.latitude, loc.longitude), 13);
    }
  }

  void addPoint(LatLng pos) {
    setState(() {
      if (points.length < 4) {
        points.add(pos);
      }
    });
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
