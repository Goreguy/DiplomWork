import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';

class MainPage extends StatefulWidget {
  final String username;

  const MainPage({
    super.key,
    required this.username,
  });

  @override
  State<MainPage> createState() => _MainPageState();
}

class _MainPageState extends State<MainPage> {

  final List<LatLng> points = [];

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

      body: FlutterMap(

        options: MapOptions(
          initialCenter: LatLng(55.75, 37.61), // Москва для примера
          initialZoom: 10,
          onTap: (_, pos) => addPoint(pos),
        ),

        children: [

          /// слой карты
          TileLayer(
            urlTemplate:
                'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
          ),

          /// маркеры точек
          MarkerLayer(
            markers: points.map((p) {
              return Marker(
                point: p,
                width: 40,
                height: 40,
                child: const Icon(
                  Icons.location_pin,
                  color: Colors.red,
                  size: 40,
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }
}