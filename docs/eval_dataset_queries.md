# Dataset Evaluasi Ablation Study (Kueri 1-5 Intent)
**Total Kueri:** 100 (20 Kueri unik per tingkat Intent)
**Domain:** Rekomendasi Pariwisata Danau Toba

Dataset ini dirancang untuk dieksekusi oleh evaluator *script* ke sistem backend RAG (Pipeline A, B, Baseline, dan Proposed) untuk menghitung metrik HR, MRR, Recall, dan NDCG.

---

## Level 1: Single Intent (1-Intent)
*Fokus pada pencarian sederhana berdasarkan 1 kondisi utama (kategori, lokasi, atau 1 fitur).*

1. Tolong carikan air terjun di sekitar kawasan Danau Toba.
2. Dimana saja lokasi wisata sejarah budaya Batak setempat?
3. Ada rekomendasi hotel berbintang di Parapat?
4. Saya mencari restoran yang menjual makanan khas Batak halal.
5. Tempat makan mana saja yang populer di kota Balige?
6. Adakah pantai berpasir putih di Pulau Samosir?
7. Coba sebutkan bukit untuk melihat panorama matahari terbit.
8. Di mana lokasi museum peninggalan ulos Batak?
9. Berikan rekomendasi penginapan berjenis guesthouse.
10. Sebutkan tempat dengan pemandangan pegunungan hijau.
11. Carikan kedai kopi dekat pelabuhan penyeberangan Ajibata.
12. Adakah lokasi wisata dengan patung purbakala ukiran batu?
13. Saya butuh rekomendasi penginapan di Tuk-Tuk Samosir.
14. Mana saja restoran yang suasananya romantis?
15. Dimana letak tempat pemandian air panas terdekat di Samosir?
16. Adakah tempat yang menjual es krim atau kuliner penutup?
17. Ingin mencari destinasi yang sepi pengunjung dan tenang.
18. Di mana pusat perbelanjaan oleh-oleh khas Toba?
19. Berikan pilihan wisata religi (gereja tua atau tempat sakral).
20. Carikan spot foto yang estetik di sekitar Tele.

---

## Level 2: Dual Intent (2-Intent)
*Fokus pada gabungan dua kondisi, biasanya Kategori + Pemandangan/Aktivitas.*

1. Carikan **hotel atau penginapan** yang punya fasilitas **kolam renang**.
2. Saya mau **berkemah (camping)** di tempat yang **suasananya sangat sunyi/tenang**.
3. Di mana ada **pantai pasir putih** yang aman untuk **wisata anak dan keluarga**?
4. Butuh **restoran** yang memiliki **pemandangan langsung ke Danau Toba**.
5. Ada rekomendasi **wisata alam** yang arsitekturnya masih berbentuk **rumah panggung tradisional**?
6. Kasih info **bukit savana** yang jalurnya **mudah diakses mobil**.
7. Ingin melihat **benda-benda kuno** di tempat bernuansa **sakral/mistis**.
8. Cari **kafe tempat ngopi** yang punya sarana **live music**.
9. Ada **penginapan resort pinggir danau** yang harganya **ramah di kantong (murah)**?
10. Butuh rekomendasi **taman bunga** berhawa **sangat sejuk berangin**.
11. Carikan **pemandian air panas belerang** yang bukanya sampai **malam hari**.
12. Di mana spot **memancing** yang juga dekat **hutan pinus**?
13. Sebutkan **restoran babi panggang** yang lokasinya ada di **pinggir tebing**.
14. Rekomendasiin **homestay** di Tuk-Tuk yang **pemiliknya ramah dan interaktif**.
15. Cari tempat wisata yang **banyak pepohonan rindang** buat berteduh dan bisa **sewa perahu**.
16. Adakah museum **Galeri ukiran kayu** yang bangunannya berbentuk **kapal bagan**?
17. Rekomendasi spot **tracking bukit** untuk berolahraga pagi dengan suasana udara yang **bersih**.
18. Mau makan di **rumah makan lesehan** yang punya menu **ikan mas arsik**.
19. Tempat belanja **kerajinan tangan tenun** yang bangunannya bernapaskan elemen **budaya asli**.
20. Ingin mencari **air terjun bertingkat** yang medannya cocok untuk **berpetualang (adventure)**.

---

## Level 3: Triple Intent (3-Intent)
*Fokus pada gabungan tiga kondisi: misalnya Kategori + Pemandangan + Suasana.*

1. Saya cari **kafe buat nongkrong** yang punya **pemandangan langsung ke danau** tapi **suasananya romantis** buat pasangan.
2. Carikan **bukit** untuk **melihat matahari terbit (sunrise)** yang medannya **gampang diakses**.
3. Ada **desa wisata** yang punya peninggalan **patung batu ukiran kuno** di mana saya bisa **belajar menenun ulos**?
4. Ingin menginap di **resort pinggir tebing** dengan nuansa **tenang dari hiruk pikuk**, serta memiliki **rute sepeda**.
5. Cari **restoran halal** di sekitar Balige yang **arsitekturnya dominan kayu tradisional** dan suasananya **sejuk berangin**.
6. Butuh **spot foto jembatan gantung** yang latarnya **hamparan sawah** dan tidak **terlalu ramai turis**.
7. Mau berwisata ke **pulau kecil tak berpenghuni**, udaranya **tropis sejuk**, dipakai khusus untuk acara **pertemuan rahasia / retreat**.
8. Tolong rekomendasikan **wisata kuliner** dengan **pemandangan senja** yang punya menu **makanan pedas andaliman**.
9. Adakah **pemandian air soda** yang kolamnya **terbuat dari batu alam** dengan hawa sekitar **menghangatkan tubuh**?
10. Cari **taman bermain outdoor** dengan lahan **berkontur bukit hijau** di mana anak bisa **naik ATV**.
11. Rekomendasi **hotel mahal/premium** yang pelayanannya bak **bintang lima**, letaknya **berhadapan dengan dermaga kapal**.
12. Butuh rekomendasi tempat berkemah di **padang rumput savana** yang malamnya dihiasi **pemandangan taburan bintang** dengan atmosfer **dingin mencekam**.
13. Adakah **museum perjuangan** yang juga menyimpan jejak **senjata kerajaan masa lalu** dengan suasana arsitektur **kuno tapi terawat**?
14. Ingin pergi ke pasar yang **menjual bumbu dapur ajaib**, bangunannya berupa **atap ijuk melengkung khas**, yang bisa sekaligus mencicipi **kue lampet**.
15. Saya cari **pantai bebatuan** yang tidak pasir, udaranya **sejuk tidak panas terik**, banyak dipakai peselancar air (windsurfing) beraktifitas.
16. Tempat jualan **kopi lintong** yang dinding cafenya **memajang lukisan lokal artis setempat**, ditambah ada **musik akustik lembut**.
17. Coba sebutkan letak peninggalan **makam raja-raja siallagan**, yang lingkungannya **dikelilingi pohon beringin**, suasananya **berwibawa**.
18. Mau keliling hutan pinus naik motor di area yang **sepanjang jalannya mulus**, minim polusi, dan gampang **menyewa mobil-mobilan kecil**.
19. Carikan rumah makan seafood yang pelayannya pakai ulos seragam, bangunannya panggung menjuntai di air tao toba, dan harganya merakyat tidak bikin jebol dompet.
20. Ingin mengunjungi tebing pandang yang bawahnya lembah terjal, biasa dipakai orang meloncat paralayang asyik, dan udara angin berhembusnya kencang tak henti.

---

## Level 4: Quad Intent (4-Intent)
*Fokus pada gabungan empat kondisi: Kategori + Kegiatan + Pemandangan/Fitur Alam + Suasana.*

1. Saya mau **restoran bersertifikat halal** (Kategori/Limitasi) di daerah Tuk-Tuk yang **arsitekturnya menyerupai bongkahan kayu alam** (Pemandangan Objek), **menjorok ke tepi hamparan danau biru** (Pemandangan Alam), dan hawanya **sangat sunyi cocok untuk bekerja** (Suasana).
2. Carikan **tempat wisata alam bebas** (Kategori) yang menyediakan **penyewaan sepeda** (Aktivitas), punya **spot foto estetik latar kincir angin** (Pemandangan), dan letaknya **sangat tersembunyi jauh dari pusat keramaian turis** (Suasana).
3. Butuh rekomendasi **hotel glamping (glamorous camping)** yang memiliki interior beda ala **suku Indian** tendanya, berada di tengah **hutan tropis rimbun**, dan sangat **aman ditinggali wanita sendirian apalagi pas malam hari**.
4. Di mana ada wisata atraksi budaya (Sigale-Gale) yang memperbolehkan **pengunjung ikut menari langsung**, pelatarannya berupa **lapangan batu ceper batu alam asli**, dan vibrasinya begitu **megah sakral menghipnotis turis asing**.
5. Mau pergi mencari wisata agro (pertanian) yang pengunjung bisa **memetik buah/sayuran sendiri pakai tangan**, lansekap panggung sawahnya terlihat berundak indah ala Bali, anginnya **menusuk tulang walau sedang siang siang terik**.
6. Tolong cari kafe *coffee shop* modern berlatar belakang lagu jazz instrumen pelan, bangunannya didominasi kaca serba terbuka (*open space*), baristanya bersedia mengajari cara seduh (V60 dll), dan pengunjung disajikan lanskap air terjun kecil buatan dalam kafe.
7. Adakah guesthouse bertingkat tinggi dengan tangga putar meliuk, menyediakan kolam air panas uap alam asli dari belerang, sangat diincar oleh pasangan bulan madu yang butuh privasi tinggi tidak ada distraksi anak kecil ribut, serta makanan sarapannya gaya eropa pancake / roti?
8. Ingin mencari destinasi bukit tertinggi agar bisa main paralayang menembus awan tebal, ada jalan setapaknya bersih tertata blok beton rapi tak berlumpur merah, cocok sekali di saat subuh hari karena nuansa damai tak tersentuh teknologi berisik, warung mienya juga mudah didapat. 
9. Rekomendasi titik pesisir pantai tao yang pasiran abu-abu basah, menyediakan olahraga *banana boat* berkelompok ramai-ramai, tidak kotor oleh tumpukan sampah sisa bakar-bakar kemah berserakan, dan sensasinya seperti liburan energi meluap-luap yang semarak sekali di akhir pekan.
10. Cari pusat sejarah peninggalan benda ukiran mitologi (berhala dewa), bangunannya tua tidak direnovasi modern karena mempertahankan *style* orisinal horor/gelapnya, kita dibolehkan meraba sebagian area arca pakai tangan, hawa di sana pun biasanya terkesan mengintimidasi yang buat merinding penasaran memacu adrenalin gembira tegang.
11. Saya ingin berburu cinderamata patung kayu tangan halus murni buatan *sculptor* asli Tobasa tanpa pabrikan kota pinggir jalan aspal tol trans Sumatera lebar tempat singgahi *tour bus* berderet parkiran panjang ramainya riuh rendah pedagang tawar-menawar seru dan ada interaksi seru belajar alat musik tradisional dari kakek-kakek yang bergelak tawa ria.
12. Adakah pemandian mata air kolam kecil sempit tak sengaja terbentuk batu besar vulkanik menyembul dari perut bumi letusan purba Toba yang hawanya segar jernih sekali sebening kaca membuat perasaan santai seakan meditasi panjang tanpa batas jam operasional berenang lama menyendiri semalaman suntuk.
13. Carikan taman keliling ramah difabel pejalan kakinya landai tak naik bertangga menyusahkan kursi roda taman bunganya ragam aster dan bogenvile tercium semerbak bau harum dari gazebo menawan yang arsitektur khas warna warni dan tak ramai cocok terapi lansia bernafas panjang tak diseruduk *traveler* rusuh muda.
14. Restoran terapung *floating resto* ala eropa klasik serasa di Venice ada tukang perahu khusus dayungkan kita santai sepoi angin membuai kelopak mata dengan desain *outdoor* bambu ikatan menempel indah yang jual sate lilit / udang galah.
15. Gua peninggalan zaman persembunyian Jepang jaring lubangnya berbatu stalaktit ke bawah tetesan air lembab suram horor tapi sekarang difasilitasi pemandu khusus eksplor gua panjang masuk merangkak kecil tak berbahaya kotor kering menyenangkan.
16. Adakah *sunset point* (titik melihat senja) tanpa harus angkat kaki mendaki (*effortless*) cukup bermobil langsung tebing kaca jernih menjorok jurang di kelilingi hamparan bukit Pusuk Buhit hijau muda mistis nan spiritual energinya kuat menghunjam kalbu rindu? 
17. Saya mau taman burung yang kicauannya bising pagi hari asri banget tanpa rekam suara (burung asli bebas lepas), kita pelajari ragam spesies burung migran dan endemik hutan hujan tropis sumatera lebat pepohonan tinggi yang ditutup awan kabut putih sore hari.
18. Wisata edukasi kerajinan lokal (Tikar Pandan) dengan atap jemuran luas membentang halaman pekarangan besar tempat pengrajin kumpul ngobrol ketawa interaksi bebas menawar kerajinan tangan dalam hangatnya *sunrise* kuning jingga pagi berlatarkan danau Toba.
19. Spot pemancingan sungai lubuk dalam (*deep water*) berbatuan cadas tajam air deras menggila tapi ada fasilitas gubuk pondok atap seng warna biru untuk istirahat pancing di mana kita memakan sendiri hasil tangkapan dibakarkan pelayan bersuasana heboh teman-teman pesta bakar lauk malam. 
20. Ingin mencari jalur sepeda lintas gunung aspal hotmix tanpa cacat jalan mulus berkelok tajam yang dikitari padang rumput ilalang tinggi *vibes* eropa pegunungan alpen hijau cerah tak berhujan agar kering melaju beriringan banyak pesepeda pro lain bergembira bersorak sorai kompetitif kencang.

---

## Level 5: Penta/Extreme Intent (5-Intent)
*Fokus pada limitasi/kendala mutlak ditambah kategori, fitur, kegiatan, dan sensasi. Baseline RAG hampir 99% dipastikan merontokkan syarat kelima atau salah kaprah seluruhnya.*

1. Saya butuh **penginapan (1)** yang harganya **ramah di kantong / murah (2)**, punya **balkon privat berjejer rapi langsung menghadap ke pelabuhan penyeberangan kapal (3)**, menyediakan layanan **penyewaan kano / perahu dayung kecil asik untuk berkeliling pelan (4)**, dan yang paling penting lingkungannya **sangat ramah balita bebas serangga serta tenang sekali saat lelap malam harinya tanpa kebisingan kelab (5)**.
2. Carikan **museum atau galeri budaya megah peradaban Toba (1)** yang lokasinya **ada di Samosir (2)**, yang menampilkan diorama sejarah rinci **Letusan supervulcan Toba purba lengkap visual artefak purba (3)**, disediakan fasilitas **pemandu wisata pakar (tour guide) berlisensi yang bisa interaktif tanya jawab dua arah santai (4)**, serta memiliki atap luar berasitektur ukiran memanjang cantik menawan *(5)*.
3. Mau restoran berkonsep **rumah kaca (1)** spesialisasi **sajian pizza bakar kyu (2)** yang pemandangan alamnya menyorot lurus ke **pantai pulau Sibandang tenang berpasir putih terang benderang menyilaukan (3)**, pengunjung dibolehkan sembari bermain pasir volly (4), dengan perasaan atmosfir hembusan kuat *ocean vibe* khas tropical (5).
4. Adakah surga tersembunyi berjenis **Air terjun perawan tersembunyi jauh (1)** yang debit luncurannya deras **bukan air terjun menempel tebing biasa tapi membelah tebing curam dua batu karang raksasa kehitaman (2)** letaknya harus **bisa ditempuh pakai motor tanpa jalan kaki jauh pegal (3)** bisa diperuntukan tempat **berendam airnya es membeku mematikan rasa lelah (4)** sejenak lari dari rutinitas serba hingar bingar kota membosankan sumpek (5). 
5. Tolong pesankan **hotel bintang paling tertinggi standar internasional mewah mentereng (1)** interior lobinya dihiasi **lampu gantung kristal mencampur corak warna tenun tradisional nyentrik unik mahal elegan (2)**, harus di posisi **titik tinggi kota Parapat berhawa pegunungan asri pagi buta berkabut membasahi kaca (3)** melayani **fasilitas fine-dining makan malam romantis intim (4)** merayakan *anniversary* dan stafnya di malam hari tak seramai siang menjaga kerahasiaan *exclusive private getaway* (5). 
6. Rekomendasi taman rekreasi air / pantai (1) bayar masuknya gratis atau sukarela saja (2) perairan danaunya memiliki dangkal landai amat bersih aman anak mengambang (3) bisa sewa pelampung bebek warni lucu berderet (4) dengan jejeran warung makan kecil di bawah naungan semilir dedaunan pinus berbisik menenangkan hati risau lelah berkendara (5).
7. Cari tempat tongkrongan kaum gen Z anak kuda (1) lokasinya di jalan utama lurus tak repot tanjakan curam (2) punya lahan api unggun *camping ground* lebar terbuka bertiup oksigen segar murni malam (3) biasa dipakai kumpul acara gitaran santuy menyusur gelap terangnya kobaran api semangat (4) ditemani pesanan minuman bir bandrek tradisional bajigur bandrek memanaskan raga santai gelak tawa bebas tanpa sungkan berekspresi heboh lepas (5).
8. Adakah pelabuhan tak komersil tersembunyi pesisir danau (1) bangunannya panggung kayu tua melapuk eksotis mempesona mata seniman foto antik (2) tempat nyender kapal nelayan kayu jukung warna warni asli yang menjual lauk langsung tangkapan net jaring jala ikan (4) suasananya tidak bising klakson Feri murni irama deburan gelora ombak memecah riak sunyi mendayu magis sendu melankolis sore senja matahari jingga mempesona redup damai sekali? (5)
9. Carikan desa adat berkonsep perkampungan utuh marga raja (1) tidak dipungut tiket masuk resmi tiket bayar loket alias di alam masyarakat terbuka (2) struktur tata rumah saling berhadapan satu sama lain khas rumah adat Batak kayu berdiri rapi simetris tertata estetis fotogenik tradisional banget (3) bisa praktek numbuk padi lesung pakai alu memeras keringat pagi olahraga lokal kampung (4) suasananya bersahaja komunal gotong royong membaur tanpa jarak sama sekali keramahtamahan tulus tak formal kaku dibatasi (5). 
10. Saya butuh spot pendakian ringan gunung / bukit santai hiking (1) cocok untuk pemula baru meniti di bawah sejam mendaki (2) puncaknya dataran luas membentang menyapu lepas 360 derajat Toba secara utuh tak terhalang objek pohon silindris satupun benar benar terbuka bebas (3) bagus buat acara memotret pre-wedding menerbangkan gaun menjuntai tiupan angin kencang merasuk mendebarkan hati seru merinding bahagia estetik ciamik tiada dua? (5)
11. Rekomendasi warung kopi lokal warga (1) pinggir tebing jurang berbatasan jurang dangkal aman miring indah ke bawah dan tak bayar parkir merepotkan (2) pemandangannya batu gamping bukit putih kering khas perbukitan sisa erupsi Toba padang belantara rerumputan kontras dengan hijaunya danau Toba permai (3) ada fasilitas penyewaan hammock asyik bergantungan lelap tidur gantung nyaman (4) bernuansa ngantuk pulas tertidur diam sunyi senyap menjauh relaksasi murni jiwa damai tentram lamat lamat sepi memanjakan hati letih lesu (5).
12. Tolong sebutkan area perbelanjaan grosir cenderamata lengkap tumpangan kaos (1) harus berada dekat dermaga ferry sehingga tak telat ke pelabuhan Samosir-Parapat memburu asyik buru-buru (2) arsitekturnya sekedar pondok papan bedeng padat berjajar sumpek tapi barangnya etnik ulos berkualitas grade A tidak murahan kain kaku jelek (3) kita bisa tawar menawar keras bergurau sengit namun akrab adu argumen tawa hangat interaktif berniaga tulus canda pelayan hangat ke wisatawan luar biasa ramai semarak (5).
13. Carikan aku wisata flora kebun perbukitan agro khusus bunga endemis (1) di balige / area pinggir jalan lintas sumatera gampang parkir gampang disinggahi rest area nyaman (2) taman bagenvile aster dan bakung tersusun mekar indah mewangi menyebar semerbak taman rimbun penuh madu asri alami merona warna cerah merah kuning meledak di mata mempesona tajam segar asri hijau (3) ada wisata tangkap lebah memeras madu alam botolan di edukasi ahli madu ramah baik bersahabat ramah interaktif menarik (4) tidak ada keramaian rombongan tur bas berjejer menjenuhkan sunyi damai saja sejuk angin murni pagi buta hening segar permai membasuh paru-paru bersih oksigen surgawi! (5)
14. Cari restoran western eropa khusus olahan hidangan pizza spagetthi berkelas pasta mahal berkelas internasional impor bumbu asli eropa *dining* (1) di lokasi tak kasat mata masuk jalan kecil berpasir tak tahu ramai orang eksklusif susah dikira tak pas umum menonjol (2) *vibe* rumah peninggalan era belanda jendela jati besar raksasa kolonial klasik estetik cat kusam eksotis (3) memfasilitasi makan memandang danau biru sendu mendung *moody* asik (4) sangat intim romantis syahdu privat tak terganggu musik pelan jazz serasa berada di dunia milik berdua tak hiraukan lain (5). 
15. Adakah pertunjukan sigale gale atraksi malam seni pergelaran berkesenian *open-air* malam di panggung terbuka luas tatanan sorot lampu etnik temaram sakral lampu api obor sekelilingnya mistis dan seram (1) khusus daerah sekitar tuktuk ringroad tak perlu nyebrang laut kapal feri repot pening tak jauh jauh capek berkendara ngantuk lelah (2) patung aslinya dari peninggalan tua mistis bukan ukiran asal pabrikan (3) penonton diizinkan melemparkan menari sersama masuk teater menyatu tanpa pembatas asyik gila semarak gemuruh penonton riuh bergembira euforia magis adat ritual komunal menari riang melepaskan penat membaur seutuhnya bebas (5).
16. Saya cari cafe bakery jual bolu teh hangat kopi susu santai nyaman bersofa empuk dalam ruangan *cozy* betah ngobrol nongkrong lesehan hangat intim (1) harus lokasinya berada di tengah desa Tomok dekat makam raja mudah dijangkau jalan raya poros jalan aspal halus bukan kelok kelok tajam miring ngeri repot nanjak nabrak lubang banyak becek meresahkan (2) memajang ornamen rotan rapi rak kayu tertata buku bacaan koran baca klasik retro estetik modern milenial tapi membaur pedesaan cantik menawan *homie vibe* hangat kekeluargaan menentramkan perasaan (3) cocok nyendiri baca novel tenang menulis buka laptop fokus meramu pikiran tak kusut hening hembusan semilir AC alam dari jendela tak dihalangi asri adem banget damai santai (5). 
17. Rekomendasikan peninggalan gereja misionaris injil nomensen tua sejarah klasik arsitektur barat abad 19an bangunan megah batu bata pres solid (1) jaraknya paling dekat tepi danau pelabuhan tanpa harus masuk kampung blusukan menyempit jauh macet masuk pasar kumuh antri bising bus parkir (2) kita masuk halamannya ditumbuhi pohon cemara pinus berbaris peneduh jalan estetik simetris rapi cantik untuk prawedding foto sakral anggun elegan mempesona klasik romantis berwibawa tinggi gagah sakral khusyuk agung spiritual meresap sendu (5).
18. Di mana kolam air hangat vulkanik pinggir kawah buatan asri batu sungai menempel indah naturalis nyatu dengan vegetasi rumput akar menjalar berkesan belum disentuh aspal sama sekali seutuhnya alami terpencil berbaur murni surgawi (1) tarif masuk seikhlasnya / minim retribusi (2) biasa digabung mancing kolam sekitar menyewa alatnya murah asik ngobrol pengelola berinteraksi seru (4) suasanya misterius sedikit temaram asap uap mengepul putih menebal kabut bau sulfur menyeruak pagi subuh udara menusuk kulit relaksasi murni raga kebal hangat menenangkan sendi linu obat jiwa damai terisolir sempurna (5)?
19. Carikan spot wisata *eco-village* kampung sadar lingkungan asri sampah bersih sekali terjaga organik daur ulang tertib indah bunga sayur organik mekar taman rapih estetik pedesaan subur tani makmur segar udara (1) kita belajar budidaya tanam memilah bibit interaksi petani asli *hands-on* kotor kotoran alam main asyik lumpur petualang edukatif banget berkesan tak sekedar foto berlalu membosankan diam (4) latar sawah menurun ke pantai toba jernih bebatuan tak berpasir berkerikil abu deburan riak air senyap hening pedalaman asli kampung nyaman syahdu suara jangkrik bernyanyi merdu beriring kawan lamat lamat nyanyian alam symphoni pengantar tidur istirahat jiwa (5).
20. Ingin berkunjung ke galeri kain tenun pewarna alam daun akar getah warna khas uis ulos asli maestro opung nenek asli bukan tenun alat mesin tekstil warna warni tak berkesan biasa (1) harga belinya jujur *fix-price* pas tak perlu lelah otot tawar ngotot ngototan capek pikiran jenuh curiga kemahalan (2) lokasi panggung kayunya serasa jaman belanda atap ijuk serpih ilalang mengkilap terik asri artistik galeri antik horison kayu jati pilar ukiran singa menatap beringas mitos berwibawa galak seram mistis auranya berlimpah wibawa purba menyengat spiritual khusyuk kental adat istiadat mendarah daging seutuhnya (5). 

---

### Cara Penggunaan:
1. Simpan kueri di atas ke dalam file berformat `.json` atau masukkan ke program python penguji Anda.
2. Hitung **HR@4, MRR@4, Recall@4, dan NDCG@4** pada masing-masing tingkatan ini (dari 1 sampai 5) di setiap mode Pipeline (Proposed, Baseline, A, B).
3. Anda akan melihat performa Baseline RAG hancur berkeping-keping seiring mendekati level ke-4 dan ke-5, sementara arsitektur **UGuideRAG (Proposed)** Anda akan tetap bertahan stabil menemukan jawaban di CSV!
