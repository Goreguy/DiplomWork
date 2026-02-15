import 'package:flutter/material.dart';
import 'main_page.dart';

class AuthPage extends StatefulWidget {
  const AuthPage({super.key});

  @override
  State<AuthPage> createState() => _AuthPageState();
}

class _AuthPageState extends State<AuthPage> {
  bool isLogin = true;

  final loginController = TextEditingController();
  final passwordController = TextEditingController();

  void submit() {
    String login = loginController.text.trim();
    String password = passwordController.text.trim();

    if (login.isEmpty || password.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Заполните все поля")),
      );
      return;
    }

    if (isLogin) {
      print("Вход: $login / $password");
    } else {
      print("Регистрация: $login / $password");
    }
    Navigator.pushReplacement(
  context,
  MaterialPageRoute(
    builder: (_) => MainPage(username: login),
    ),
    );


    // здесь позже будет запрос к backend
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[100],
      body: Center(
        child: Container(
          width: 350,
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            boxShadow: const [
              BoxShadow(
                blurRadius: 10,
                color: Color.fromARGB(31, 0, 0, 0),
              )
            ],
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [

              /// Заголовок
              Text(
                isLogin ? "Вход" : "Регистрация",
                style: const TextStyle(
                  fontSize: 26,
                  fontWeight: FontWeight.bold,
                ),
              ),

              const SizedBox(height: 20),

              /// Логин
              TextField(
                controller: loginController,
                decoration: const InputDecoration(
                  labelText: "Логин",
                  border: OutlineInputBorder(),
                ),
              ),

              const SizedBox(height: 12),

              /// Пароль
              TextField(
                controller: passwordController,
                obscureText: true,
                decoration: const InputDecoration(
                  labelText: "Пароль",
                  border: OutlineInputBorder(),
                ),
              ),

              const SizedBox(height: 20),

              /// Кнопка
              ElevatedButton(
                onPressed: submit,
                style: ElevatedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 45),
                ),
                child: Text(isLogin ? "Войти" : "Зарегистрироваться"),
              ),

              const SizedBox(height: 10),

              /// Переключение режима
              TextButton(
                onPressed: () {
                  setState(() {
                    isLogin = !isLogin;
                  });
                },
                child: Text(
                  isLogin
                      ? "Нет аккаунта? Зарегистрироваться"
                      : "Уже есть аккаунт? Войти",
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}