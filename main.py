import pygame
from pytmx.util_pygame import load_pygame
import pkg_resources
from random import randint
import sys

WIDTH = 1280
HEIGHT = 720
TILE_SIZE = 64
BG_COLOR = "#55B4FF"

def path(semi_path):
    return pkg_resources.resource_filename(__name__, semi_path)

class Timer:
    
    def __init__(self, durata, funzione = None, ripetizione = False, autostart = False):
        
        self.durata = durata
        self.funzione = funzione
        self.inizio_timer = 0
        self.active = False
        self.ripeti = ripetizione
        self.autostart = autostart
        
        if self.autostart:
            self.attiva()

    def __bool__(self):
        return self.active  # chiamata in un if statement, questa class farà return di un valore

    def attiva(self):
        self.active = True
        self.inizio_timer = pygame.time.get_ticks()

    def disattiva(self):
        self.active = False
        self.inizio_timer = 0
        
        if self.ripeti:
            self.attiva()

    def update(self):
        if self.active:
            tempo_corrente = pygame.time.get_ticks()
            if tempo_corrente - self.inizio_timer >= self.durata:
                
                if self.funzione and self.inizio_timer != 0:
                    self.funzione()
            
                self.disattiva()

class Sprite(pygame.sprite.Sprite):
    
    def __init__(self, posizione, immagine, gruppo):

        super().__init__(gruppo)
        
        self.image = immagine
        self.rect = self.image.get_frect(topleft = posizione)

class Tutte_sprite(pygame.sprite.Group):

    def __init__(self):
        super().__init__()

        self.schermo = pygame.display.get_surface()
        self.offset = pygame.Vector2()

    def draw(self, posizione_giocatore):

        self.offset.x = -(posizione_giocatore[0] - WIDTH / 2)
        self.offset.y = -(posizione_giocatore[1] - HEIGHT / 2)
        
        for sprite in self:
            self.schermo.blit(sprite.image, sprite.rect.topleft + self.offset)

class Animazioni(Sprite):

    def __init__(self, immagine, posizione, gruppo):
        
        self.frames = immagine
        self.frame_index = 0
        self.vel_animazione = 10
        super().__init__(posizione, self.frames[self.frame_index], gruppo) 

    def animato(self, delta_time):

        self.frame_index += self.vel_animazione * delta_time   
        self.image = self.frames[int(self.frame_index) % len(self.frames)]

class Nemico(Animazioni):

    def __init__(self, immagine, posizione, gruppo):
        super().__init__(immagine, posizione, gruppo)

        self.timer_fine = Timer(200, funzione = self.kill)

    def destroy(self):

        self.timer_fine.attiva()
        self.vel_animazione = 0
        self.image = pygame.mask.from_surface(self.image).to_surface()
        self.image.set_colorkey("black")

    def update(self, delta_time):
        
        self.timer_fine.update()

        if not self.timer_fine:

            self.movimento(delta_time)
            self.animato(delta_time)
            self.interazione()

class Giocatore(Animazioni):

    def __init__(self, posizione, gruppo, sprite_collisione, frames):

        super().__init__(frames, posizione, gruppo)

        self.direzione = pygame.Vector2()
        self.velocità = 300
        self.gravità = 50
        self.sul_terreno = True
        self.collisioni_sprite = sprite_collisione
        self.image_flip = False
        self.tipo_immagini = 0

        self.lista_salto = [pygame.image.load(path("immagini/giocatore/jump.png")), pygame.image.load(path("immagini/giocatore/jump.png"))]
        self.lista_caduta = [pygame.image.load(path("immagini/giocatore/fall.png")), pygame.image.load(path("immagini/giocatore/fall.png"))]
        self.lista_idle = [pygame.image.load(path(f"immagini/giocatore/idle/{i}.png")).convert_alpha() for i in range(12)]
        self.salto = pygame.mixer.Sound(path("immagini/salto.mp3"))

    def input(self):

        chiave = pygame.key.get_pressed()
        self.direzione.x = int(chiave[pygame.K_RIGHT] - chiave[pygame.K_LEFT])

        if chiave[pygame.K_SPACE] and self.sul_terreno:
            self.salto.play()
            self.direzione.y = -23

    def movimento(self, delta_time):

        self.rect.x += self.direzione.x * self.velocità * delta_time
        self.collisioni("orizzontale")
        self.rettangolo_ver_col_des = pygame.FRect((0,0), (4, self.rect.height)).move_to(midleft = self.rect.midright)
        self.rettangolo_ver_col_sin = pygame.FRect((0,0), (4, self.rect.height)).move_to(midright = self.rect.midleft)

        self.direzione.y += self.gravità * delta_time
        self.rect.y += self.direzione.y * self.gravità * delta_time
        self.collisioni("verticale")

    def collisioni(self, direzione):

        for sprite in self.collisioni_sprite:
            if sprite.rect.colliderect(self.rect):  
                
                if direzione == "orizzontale":
                    if self.direzione.x > 0:                
                        self.rect.right = sprite.rect.left  
                    
                    if self.direzione.x < 0:                 
                        self.rect.left = sprite.rect.right  

                if direzione == "verticale":
                    
                    if self.direzione.y > 0:
                        self.rect.bottom = sprite.rect.top
                    
                    if self.direzione.y < 0:
                        self.rect.top = sprite.rect.bottom
                    
                    self.direzione.y = 0

    def check_salto(self):

        self.rettangolo_verifica = pygame.FRect((0,0), (self.rect.width, 2)).move_to(midtop = self.rect.midbottom)
        self.rettangolo_ver_col_sop = pygame.FRect((0,0), (self.rect.width, 2)).move_to(midbottom = self.rect.midtop)
        
        self.sul_terreno = True if self.rettangolo_verifica.collidelist([sprite.rect for sprite in self.collisioni_sprite]) >= 0 else False

    def animato(self, delta_time):

        if self.direzione.y < 0 and self.sul_terreno == False:
            self.frames = self.lista_salto

        if self.direzione.y > 0 and self.sul_terreno == False:
            self.frames = self.lista_caduta
    
        if self.sul_terreno == True:
            self.frames = game.frames_camminata

        if self.direzione.x:                             # quando si muove verifichiamo che stia andando in un veros flippando l'immagine
            self.image_flip = self.direzione.x < 0
            
        if not self.direzione.x and self.sul_terreno:
            self.frames = self.lista_idle               # quando il giocatore si trova a terra e fermo, farà un'animazione di waiting 

        self.frame_index += self.vel_animazione * delta_time
        self.frame_index = 1 if not self.sul_terreno else self.frame_index
            

        self.image = self.frames[int(self.frame_index) % len(self.frames)]
        self.image = pygame.transform.flip(self.image, self.image_flip, False)

    def update(self, delta_time):
        
        self.animato(delta_time)
        self.check_salto()
        self.input()
        self.movimento(delta_time)

class Proiettile(Sprite):

    def __init__(self, posizione, immagine, direzione, gruppo):
        super().__init__(posizione, immagine, gruppo)

        self.direzione = direzione
        self.velocità_proiettile = 550
        self.image = pygame.transform.flip(self.image, direzione == -1, False)
        self.proiettile = True

        self.timer_fine = Timer(200, funzione = self.kill)

    def destroy(self):

        self.timer_fine.attiva()
        self.vel_animazione = 0
        self.image = pygame.mask.from_surface(self.image).to_surface()
        self.image.set_colorkey("black")

    def update(self, delta_time):
        
        self.timer_fine.update()

        if not self.timer_fine:
            self.rect.x += self.direzione * self.velocità_proiettile * delta_time

        self.rettangolo_ver_col = pygame.FRect((0,0), (self.rect.width, 2)).move_to(midbottom = self.rect.midtop)
        self.rettangolo_ver_col_des = pygame.FRect((0,0), (4, self.rect.height / 2)).move_to(midleft = self.rect.midright)
        self.rettangolo_ver_col_sin = pygame.FRect((0,0), (4, self.rect.height / 2)).move_to(midright = self.rect.midleft)
        self.rettangolo_ver_col_sot = pygame.FRect((0,0), (self.rect.width, 4)).move_to(midtop = self.rect.midbottom)

        if self.rect.x > 4000 or self.rect.x < -150:
            self.kill()

class Mostro(Nemico):

    def __init__(self, immagine, rettangolo, gruppo):
        super().__init__(immagine, rettangolo.topleft, gruppo)

        self.rect.bottomleft = rettangolo.bottomleft  
        self.rettangolo_principale = rettangolo
        self.velocità = randint(60, 100)
        self.direzione = 1

    def interazione(self):

        if not self.rettangolo_principale.contains(self.rect):           
            
            self.direzione = -self.direzione
            self.frames = [pygame.transform.flip(immagine, True, False) for immagine in self.frames]

    def movimento(self, delta_time):

        self.rect.x += self.direzione * self.velocità * delta_time

        self.rettangolo_ver_col = pygame.FRect((0,0), (self.rect.width + 20, 4)).move_to(midbottom = self.rect.midtop)
        self.rettangolo_ver_col_des = pygame.FRect((0,0), (4, self.rect.height)).move_to(midleft = self.rect.midright)
        self.rettangolo_ver_col_sin = pygame.FRect((0,0), (4, self.rect.height)).move_to(midright = self.rect.midleft)
        self.rettangolo_ver_col_sot = pygame.FRect((0,0), (self.rect.width + 40, 4)).move_to(midtop = self.rect.midbottom)

class Acqua(Animazioni):

    def __init__(self, immagine, posizione, gruppo):
        super().__init__(immagine, posizione, gruppo)

        self.velocità = 20

    def update(self, delta_time):
        self.rect.y += -(self.velocità * delta_time)

class Morte(pygame.sprite.Sprite):

    def __init__(self, lista_immagini, posizioni, causa_morte, gruppo):
        super().__init__(gruppo)

        self.lista_immagini = lista_immagini
        self.index = 0
        self.image = self.lista_immagini[self.index]            
        self.rect = self.image.get_frect(center = posizioni)
        self.causa_morte = causa_morte

    def update(self, delta_time):
        
        self.index += 20 * delta_time

        if self.index < len(self.lista_immagini):
            self.image = self.lista_immagini[int(self.index)]  
        
        else:
            game.menu(self.causa_morte)


class Gioco:
    
    def __init__(self):

        pygame.init()
        
        self.schermo = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Sky Climb")
        self.clock = pygame.time.Clock()
        self.running = False

        self.timer_inizio = 0
        self.tempo_sopravvivenza = 0
        self.tempo_totale = 0
        self.tempo_lvl_1 = 0
        self.tempo_lvl_2 = 0
        self.tempo_lvl_3 = 0

        self.mostri_uccisi = set()
        self.totale_mostri_uccisi = 0

        self.index = 1
        self.vittoria = False
        self.lista_launcher = []

        self.dizionario_morti = {
            "vittoria": "You really won this round\n without cheats?",
            "morte_proiettile": "You were laid down by a\nbullet that was hanging there.",
            "morte_mostro":  "You got deleted by a\nlittle creature. Be ashamed.",
            "annegato": "You drown. Bruh!",
            "fine_gioco": "How did you get here?\nYou have finished this game!"
        }

        self.timer_proiettili = Timer(randint(1500, 3000), funzione = self.proiettili, autostart = True, ripetizione = True)

        self.tutte_sprite = Tutte_sprite()
        self.sprite_vittoria = pygame.sprite.Group()
        self.sprite_collisioni = pygame.sprite.Group()
        self.sprite_nemici = pygame.sprite.Group()

        self.carica_immagini()
        self.setup()

    def carica_immagini(self): 

        self.font = pygame.font.Font(path("immagini/Oxanium-Bold.ttf"), 40)

        self.frames_camminata = [pygame.image.load(path(f"immagini/giocatore/camminata/{i}.png")).convert_alpha() for i in range(12)]

        self.frames_morte = [pygame.image.load(path(f"immagini/morte/{i}.png")) for i in range(7)]

        self.frame_mostro_0 = pygame.image.load(path("immagini/0.png")).convert_alpha()
        self.frame_mostro_1 = pygame.image.load(path("immagini/1.png")).convert_alpha()
        self.frames_mostro = [self.frame_mostro_0, self.frame_mostro_1]

        self.frame_proiettile = pygame.image.load(path("immagini/bullet.png")).convert_alpha()

        self.acqua = pygame.image.load(path("immagini/acqua.png")).convert_alpha()
        self.frames_acqua = [self.acqua, self.acqua]

        self.musica = pygame.mixer.Sound(path("immagini/music.mp3"))
        self.musica.set_volume(0.8)

    def setup(self):

        if self.vittoria == "vittoria" or self.vittoria == "fine_gioco":
            self.index += 1

        try:
            mappa = load_pygame(path(f"data/maps/mondo{self.index}.tmx"))

            for x, y, immagine in mappa.get_layer_by_name("main").tiles(): 
                Sprite((x * TILE_SIZE, y * TILE_SIZE), immagine, (self.tutte_sprite, self.sprite_collisioni))

            for x, y, immagine in mappa.get_layer_by_name('decorazioni').tiles():
                Sprite((x * TILE_SIZE, y * TILE_SIZE), immagine, self.tutte_sprite)

            for oggetto in mappa.get_layer_by_name("Entities"):
                
                if oggetto.name == "Player":
                    self.giocatore = Giocatore((oggetto.x, oggetto.y), self.tutte_sprite, self.sprite_collisioni, self.frames_camminata)
                
                elif oggetto.name == "Launcher":
                    self.lista_launcher.append((oggetto.x, oggetto.y))
                
                elif oggetto.name == "Vittoria":
                    self.rettangolo_vittoria = Sprite((oggetto.x, oggetto.y), pygame.Surface((oggetto.width, oggetto.height)), self.sprite_vittoria)

                elif oggetto.name == "Border":
                    Sprite((oggetto.x, oggetto.y), pygame.Surface((oggetto.width, oggetto.height)), self.sprite_collisioni)

                else:
                    Mostro((self.frames_mostro), 
                        pygame.FRect(oggetto.x, oggetto.y, oggetto.width, oggetto.height),
                        (self.tutte_sprite, self.sprite_nemici))

            self.acqua_oggetto = Acqua(self.frames_acqua, (-600, 3350), self.tutte_sprite) 

        except FileNotFoundError:
            pygame.quit()
            sys.exit()

    def collisioni(self):

        if self.giocatore.rect.colliderect(self.rettangolo_vittoria) and self.index < 3:  
            self.menu("vittoria")

        elif self.giocatore.rect.colliderect(self.rettangolo_vittoria) and self.index == 3:
            self.menu("fine_gioco")

        if self.giocatore.rect.colliderect(self.acqua_oggetto):
            
            Morte(self.frames_morte, self.giocatore.rect.center, "annegato", self.tutte_sprite)
            self.giocatore.kill()


        for mostro in self.sprite_nemici:

            if self.giocatore.rettangolo_verifica.colliderect(mostro.rettangolo_ver_col): 

                mostro.destroy()
                self.giocatore.direzione.y = -5
                
                if not hasattr(mostro, "proiettile"):
                    self.mostri_uccisi.add((mostro.rect.x, mostro.rect.y))


            if self.giocatore.rettangolo_ver_col_des.colliderect(mostro.rettangolo_ver_col_sin) or \
                self.giocatore.rettangolo_ver_col_sin.colliderect(mostro.rettangolo_ver_col_des) or \
                self.giocatore.rettangolo_ver_col_sop.colliderect(mostro.rettangolo_ver_col_sot):
                
                tipo_morte = "morte_proiettile" if hasattr(mostro, "proiettile") else "morte_mostro"
                
                Morte(self.frames_morte, self.giocatore.rect.center, tipo_morte, self.tutte_sprite) # passiamo i frames della scomparsa, la posizione del player, il tipo di morte e il gruppo
                self.giocatore.kill()

      
            if mostro.rect.colliderect(self.acqua_oggetto):
                mostro.destroy() if not hasattr(mostro, "proiettile") else mostro.kill()

    def proiettili(self):

        for launcher in self.lista_launcher:

            direzione = -1 if launcher[0] > (WIDTH / 2) else 1
            x = launcher[0] + self.frame_proiettile.get_width() if direzione == 1 else launcher[0] - self.frame_proiettile.get_width()
            Proiettile((x, launcher[1]), self.frame_proiettile, direzione, (self.tutte_sprite, self.sprite_nemici))      

    def menu(self, vittoria):

        self.musica.stop()
        self.running = False
        self.tempo_sopravvivenza = self.tempo_partita()
        self.vittoria = vittoria

        if self.index == 1:
            self.tempo_lvl_1 = self.tempo_sopravvivenza

        elif self.index == 2:
            self.tempo_lvl_2 = self.tempo_sopravvivenza

        elif self.index == 3:
            self.tempo_lvl_3 = self.tempo_sopravvivenza

    def tempo_partita(self):
        self.tempo = pygame.time.get_ticks() / 1000 - self.timer_inizio
        self.tempo = round(self.tempo, 2)

        return self.tempo
    
    def fine(self):
                
        self.schermo.fill("orange")
        self.tutte_sprite.empty()

        text = self.dizionario_morti.get(self.vittoria, "Press Return to start the game.")   # valore di default quando non c'è una morte

        stats = self.font.render(f"{text}", True, "Black")
        rect = stats.get_frect(center = (WIDTH / 2, HEIGHT / 2  - (stats.get_height() * 2)))
        self.schermo.blit(stats, rect)
        
        if self.vittoria == "fine_gioco":
            tempo_e_nemici = self.font.render(f"Stats:\nTotal opp. eliminated: {self.totale_mostri_uccisi + self.mostri_uccisi.__len__()}\nTime to complete the level 1: {round(self.tempo_lvl_1, 2)} secs\nTime to complete the level 2: {round(self.tempo_lvl_2, 2)} secs\nTime to complete the level 3: {round(self.tempo_lvl_3, 2)} secs", True, "black")
            rect_2 = stats.get_frect(center = (WIDTH / 2 , HEIGHT / 2 + 20))        # usiamo stats come rettangolo per mantenere le statistiche allineate con il titolo

        else:
            tempo_e_nemici = self.font.render(f"Stats:\nOpponents eliminated: {self.mostri_uccisi.__len__()}\nTime survived: {self.tempo_sopravvivenza} secs", True, "black")
            rect_2 = stats.get_frect(center = (WIDTH / 2 , HEIGHT / 2 + 20))
        
        self.schermo.blit(tempo_e_nemici, rect_2)

    def run(self):

        while True:
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if self.running == False:
                    
                    self.timer_inizio = pygame.time.get_ticks() / 1000

                    if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:

                        self.totale_mostri_uccisi += self.mostri_uccisi.__len__()   # modifichiamo i mostri uccisi in totale

                        self.mostri_uccisi.clear()  # clear dei mostri uccisi per ricominciare da zero
                        self.lista_launcher.clear() # clear delle posizioni dei proiettili allo spawn delle coordinate

                        self.sprite_nemici.empty()      # eliminiamo i nemici
                        self.sprite_vittoria.empty()    # eliminiamo il rettangolo per la collisione per la vittoria
                        self.sprite_collisioni.empty()  # eliminiamo tutte le tile

                        self.setup()                    # chiamiamo self.setup per far apparire i nuovi livelli in caso di vittoria
                        self.running = True
                        self.musica.play(loops = -1)


            delta_time = self.clock.tick() / 1000

            if self.running:

                self.tutte_sprite.update(delta_time)
                self.schermo.fill(BG_COLOR)

                self.collisioni()
                self.timer_proiettili.update()

                self.tempo_sopravvivenza = self.tempo_partita()
                self.tutte_sprite.draw(self.giocatore.rect.center)

            else:
                self.fine()

            pygame.display.update()
         
    
if __name__ == "__main__":
    game = Gioco()
    game.run()


# pyinstaller --onefile --add-data "data/graphics/tilemap.png;data/graphics" --add-data "data/graphics/tilemap2.png;data/graphics" --add-data "data/maps/mondo1.tmx;data/maps" --add-data "data/maps/mondo2.tmx;data/maps" --add-data "data/maps/mondo3.tmm;data/maps" --add-data "data/tilesets/tileset.tsx;data/tilesets" --add-data "data/tilesets/tileset2.tsx;data/tilesets" --add-data "immagini/0.png;immagini" --add-data "immagini/1.png;immagini" --add-data "immagini/acqua.png;immagini" --add-data "immagini/bullet.png;immagini" --add-data "immagini/music.mp3;immagini" --add-data "immagini/Oxanium-Bold.ttf;immagini" --add-data "immagini/salto.mp3;immagini" --add-data "immagini/morte/0.png;immagini/morte" --add-data "immagini/morte/1.png;immagini/morte" --add-data "immagini/morte/2.png;immagini/morte" --add-data "immagini/morte/3.png;immagini/morte" --add-data "immagini/morte/4.png;immagini/morte" --add-data "immagini/morte/5.png;immagini/morte" --add-data "immagini/morte/6.png;immagini/morte" --add-data "immagini/giocatore/fall.png;immagini/giocatore" --add-data "immagini/giocatore/jump.png;immagini/giocatore" --add-data "immagini/giocatore/camminata/0.png;immagini/giocatore/camminata" --add-data "immagini/giocatore/camminata/1.png;immagini/giocatore/camminata" --add-data "immagini/giocatore/camminata/2.png;immagini/giocatore/camminata" --add-data "immagini/giocatore/camminata/3.png;immagini/giocatore/camminata" --add-data "immagini/giocatore/camminata/4.png;immagini/giocatore/camminata" --add-data "immagini/giocatore/camminata/5.png;immagini/giocatore/camminata" --add-data "immagini/giocatore/camminata/6.png;immagini/giocatore/camminata" --add-data "immagini/giocatore/camminata/7.png;immagini/giocatore/camminata" --add-data "immagini/giocatore/camminata/6.png;immagini/giocatore/camminata" --add-data "immagini/giocatore/camminata/9.png;immagini/giocatore/camminata" --add-data "immagini/giocatore/camminata/10.png;immagini/giocatore/camminata" --add-data "immagini/giocatore/camminata/11.png;immagini/giocatore/camminata" --add-data "immagini/giocatore/idle/0.png;immagini/giocatore/idle" --add-data "immagini/giocatore/idle/1.png;immagini/giocatore/idle" --add-data "immagini/giocatore/idle/2.png;immagini/giocatore/idle" --add-data "immagini/giocatore/idle/3.png;immagini/giocatore/idle" --add-data "immagini/giocatore/idle/4.png;immagini/giocatore/idle" --add-data "immagini/giocatore/idle/5.png;immagini/giocatore/idle" --add-data "immagini/giocatore/idle/6.png;immagini/giocatore/idle" --add-data "immagini/giocatore/idle/7.png;immagini/giocatore/idle" --add-data "immagini/giocatore/idle/8.png;immagini/giocatore/idle" --add-data "immagini/giocatore/idle/9.png;immagini/giocatore/idle" --add-data "immagini/giocatore/idle/10.png;immagini/giocatore/idle" --add-data "immagini/giocatore/idle/11.png;immagini/giocatore/idle" -F -w -i icona.ico main.py
