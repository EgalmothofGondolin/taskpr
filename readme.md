# Ai Finance Projesi - E-Marketing Mikroservisleri

Bu proje, kullanıcı yönetimi, kimlik doğrulama/yetkilendirme, ürün yönetimi, alışveriş sepeti ve sipariş yönetimi gibi temel e-ticaret fonksiyonlarını iki ayrı mikroservis (`user_service` ve `product_service`) aracılığıyla sunan bir uygulamadır. Proje, Docker ve Docker Compose kullanılarak kolayca kurulup çalıştırılabilir. Ayrıca Streamlit tabanlı bir frontend arayüzü de içermektedir.

## Projenin Amacı

Bu proje, mikroservis mimarisinin temel prensiplerini uygulamalı olarak göstermeyi, kullanıcı ve ürün yönetimi gibi modülleri bağımsız servisler olarak geliştirmeyi ve bu servislerin JWT tabanlı kimlik doğrulama ile nasıl etkileşime girdiğini sergilemeyi hedefler.

## Genel Mimari

*   **User Service:** Kullanıcı kaydı, girişi, JWT token yönetimi, rol tabanlı yetkilendirme, adres ve iletişim bilgileri yönetiminden sorumludur.
*   **Product Service:** Ürün, alışveriş sepeti ve sipariş yönetiminden sorumludur. Kimlik doğrulama için `user_service` tarafından üretilen JWT'leri kullanır.
*   **Frontend Streamlit:** Kullanıcıların servislerle etkileşime girebileceği basit bir web arayüzü sunar.
*   **PostgreSQL:** Her iki mikroservis için veri depolama çözümü olarak kullanılır.
*   **Redis:** `user_service` tarafından JWT token blacklist (logout işlemi için) mekanizmasında cache olarak kullanılır.

## Kullanılan Teknolojiler

*   **Backend (Her İki Servis):**
    *   Dil: Python 3.12
    *   Framework: FastAPI
    *   ORM: SQLAlchemy
    *   Veri Doğrulama/Serileştirme: Pydantic
    *   ASGI Sunucu: Uvicorn
*   **Kimlik Doğrulama & Yetkilendirme:**
    *   JWT (python-jose), OAuth2PasswordBearer
    *   Şifreleme: Passlib (bcrypt)
*   **Veritabanı:** PostgreSQL (Alpine tabanlı imaj)
*   **Cache:** Redis (Alpine tabanlı imaj)
*   **Frontend:** Streamlit
*   **Konteynerleme:** Docker, Docker Compose
*   **Test:** Pytest

## Proje Yapısı
├── docker-compose.yml # Servisleri ve altyapıyı yönetir
├── .env # Ana ortam değişkenleri
├── init-scripts/ # PostgreSQL için başlangıç script'leri
│ └── init-all-dbs.sh
├── user_service/ # User Service kaynak kodları, Dockerfile, testler
│ ├── app/
│ ├── tests/
│ ├── Dockerfile
│ ├── Dockerfile.test
│ └── requirements.txt
├── product_service/ # Product Service kaynak kodları, Dockerfile, testler
│ ├── app/
│ ├── tests/
│ ├── Dockerfile
│ ├── Dockerfile.test
│ └── requirements.txt
├── frontend_streamlit/ # Streamlit frontend kaynak kodları, Dockerfile
│ ├── Home.py
│ ├── pages/
│ ├── Dockerfile
│ └── requirements.txt
└── README.md # Bu dosya


## Kurulum ve Çalıştırma

### Ön Gereksinimler

*   [Docker](https://docs.docker.com/get-docker/)
*   [Docker Compose](https://docs.docker.com/compose/install/)

### Adım Adım Kurulum

1.  **Projeyi Klonlayın:**
    ```bash
    git clone <repository_url> # Reponuzun URL'sini buraya yazın
    cd proje-klasor-adi
    ```

2.  **`.env` Dosyasını Oluşturun ve Yapılandırın:**
    Proje kök dizininde `.env.example` adındaki dosyayı, `.env` olarak değiştirin ve aşağıdakine benzer bir içerikle doldurun. **Özellikle şifreleri kendi güvenli değerlerinizle değiştirin**:

    ```dotenv
    # Proje Kök Dizinindeki .env Dosyası

    # PostgreSQL Ayarları
    POSTGRES_HOST=db
    POSTGRES_PORT=5432
    POSTGRES_USER=adminuser         # PostgreSQL kullanıcı adı
    POSTGRES_PASSWORD=adminpassword # GÜVENLİ BİR ŞİFRE SEÇİN!

    # Veritabanı Adları (init-scripts/init-all-dbs.sh tarafından oluşturulacak)
    USER_SERVICE_DB_NAME=user_service_db
    USER_SERVICE_DB_TEST_NAME=user_service_db_test
    PRODUCT_SERVICE_DB_NAME=product_service_db
    PRODUCT_SERVICE_DB_TEST_NAME=product_service_db_test

    # User Service için Ortam Değişkenleri
    USER_SERVICE_SECRET_KEY="COK_GIZLI_VE_GUCLU_BIR_USER_SERVICE_ANAHTARI" # Örn: openssl rand -hex 32
    USER_SERVICE_ALGORITHM="HS256"
    USER_SERVICE_ACCESS_TOKEN_EXPIRE_MINUTES=60

    # Product Service için JWT Ayarları (User Service ile AYNI OLMALI!)
    PRODUCT_SERVICE_SECRET_KEY=${USER_SERVICE_SECRET_KEY} # User Service ile aynı
    PRODUCT_SERVICE_ALGORITHM=${USER_SERVICE_ALGORITHM}   # User Service ile aynı
    PRODUCT_SERVICE_ACCESS_TOKEN_EXPIRE_MINUTES=${USER_SERVICE_ACCESS_TOKEN_EXPIRE_MINUTES}

    # İlk Admin Kullanıcı Bilgileri (User Service ilk çalıştığında oluşturulur)
    FIRST_SUPERUSER_USERNAME=admin
    FIRST_SUPERUSER_PASSWORD=YourSecureAdminPassword123! # EN AZ 8 KARAKTERLİ GÜVENLİ BİR ŞİFRE
    FIRST_SUPERUSER_EMAIL=admin@example.com

    # Redis Ayarları (User Service Logout Blacklist için)
    USER_SERVICE_REDIS_HOST=redis
    USER_SERVICE_REDIS_PORT=6379
    USER_SERVICE_REDIS_BLACKLIST_DB=1      # Ana servis için Redis DB
    USER_SERVICE_REDIS_BLACKLIST_DB_TEST=2 # Test servisi için Redis DB
    ```

3.  **Başlangıç Script'ine Çalıştırma Yetkisi Verin:**
    `init-scripts` klasöründeki `.sh` dosyasına çalıştırma yetkisi verin (Linux/macOS için):
    ```bash
    chmod +x init-scripts/init-all-dbs.sh
    ```

4.  **Docker Konteynerlerini Başlatın:**
    Proje kök dizinindeyken aşağıdaki komutu çalıştırın:
    ```bash
    docker-compose up --build -d
    ```
    *   `--build`: İmajları (yeniden) oluşturur.
    *   `-d`: Konteynerleri arka planda (detached mode) çalıştırır. Logları görmek için bu parametreyi kaldırabilirsiniz.

    İlk başlatmada, PostgreSQL veritabanları oluşturulacak, `user_service` tabloları ve başlangıç verileri (roller, izinler, admin kullanıcı) yazılacaktır. Bu işlem biraz zaman alabilir. Servislerin loglarını `docker-compose logs -f <servis_adi>` (örn: `docker-compose logs -f user_service_app`) ile takip edebilirsiniz.

## Uygulamaya Erişim

*   **Frontend Arayüzü (Streamlit):**
    *   [http://localhost:8501](http://localhost:8501)
*   **User Service API Dokümantasyonu (Swagger UI):**
    *   [http://localhost:8000/docs](http://localhost:8000/docs)
*   **Product Service API Dokümantasyonu (Swagger UI):**
    *   [http://localhost:8001/docs](http://localhost:8001/docs)

## Varsayılan Admin Kullanıcısı

*   **Kullanıcı Adı:** `.env` dosyasındaki `FIRST_SUPERUSER_USERNAME` değeri (örn: `admin`)
*   **Şifre:** `.env` dosyasındaki `FIRST_SUPERUSER_PASSWORD` değeri.
*   Bu kullanıcı ile `user_service` üzerinden giriş yaparak (`http://localhost:8000/docs` adresindeki `/auth/login` endpoint'i veya frontend arayüzü üzerinden) admin yetkisi gerektiren işlemleri yapabilirsiniz.

## Testlerin Çalıştırılması

Testleri çalıştırmak için aşağıdaki komutları kullanabilirsiniz:

*   **User Service Testleri:**
    ```bash
    docker-compose run --rm user_service_tests
    ```
    Veya eğer konteynerler zaten çalışıyorsa:
    ```bash
    docker-compose exec user_service_tester pytest -vv -s /code/tests
    ```
*   **Product Service Testleri:**
    ```bash
    docker-compose run --rm product_service_tests
    ```
    Veya eğer konteynerler zaten çalışıyorsa:
    ```bash
    docker-compose exec product_service_tester pytest -vv -s /code/tests
    ```

## Projenin Durdurulması

*   Konteynerleri durdurmak ve kaldırmak için (veritabanı volume'leri korunur):
    ```bash
    docker-compose down
    ```
*   Konteynerleri durdurmak, kaldırmak VE **tüm volume'leri (veritabanı dahil)** silmek için (temiz bir başlangıç için):
    ```bash
    docker-compose down -v
    ```

## API Endpointleri (Genel Bakış)

Her servisin kendi `/docs` endpoint'inde detaylı API dokümantasyonu bulunmaktadır.

### User Service Ana Endpoint Grupları:
*   `/auth`: Login, Logout, Token Kontrolü, Mevcut Kullanıcı Bilgileri/İzinleri
*   `/authz`: Yetki Kontrolleri (Role/İzin Sahip mi?)
*   `/users`: Kullanıcı Yönetimi (CRUD, Şifre Sıfırlama, Rol Atama)
*   `/addresses`: Mevcut Kullanıcı Adres Yönetimi (CRUD)
*   `/contacts`: Mevcut Kullanıcı İletişim Bilgileri Yönetimi (CRUD)
*   `/roles`: Rol Yönetimi (Listeleme, İzin Güncelleme - Admin)
*   `/permissions`: İzin Listeleme (Admin)

### Product Service Ana Endpoint Grupları:
*   `/products`: Ürün Yönetimi (CRUD - Admin Yetkisi Gerekli)
*   `/cart`: Mevcut Kullanıcının Alışveriş Sepeti Yönetimi
*   `/orders`: Mevcut Kullanıcının Sipariş Yönetimi
*   `/reports`: Mevcut Kullanıcının Sipariş Raporları
*   `/categories`: Admin İçin Sipariş Yönetimi


## Katmanlı Mimari

Her iki backend servisi de (user_service, product_service) kodun okunabilirliğini ve bakımını kolaylaştırmak amacıyla katmanlı bir mimari (routers, services, repositories/CRUD, models, schemas/Pydantic) takip etmeye çalışır.

## Ek Notlar

*   `product_service` içindeki admin yetki kontrolleri şu an için JWT token'ındaki role dayanmaktadır ve `user_service` tarafından doğrulanmış kullanıcı bilgilerine güvenir. Daha karmaşık yetkilendirme senaryoları için ek mekanizmalar geliştirilebilir.
