from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time as tempo
from selenium.webdriver.common.action_chains import ActionChains
import sqlite3 as sql

USER_AGENT = 'Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'


def creation_database():
    """Créer la base de données
    """
    conn = sql.connect("polytechDatabase.db")
    curs = conn.cursor()
    curs.execute("DROP TABLE IF EXISTS Prof")
    curs.execute("CREATE TABLE  Prof (nom VARCHAR PRIMARY KEY)")
    curs.execute("DROP TABLE IF EXISTS Article")
    curs.execute(
        "CREATE TABLE Article (idArticle VARCHAR PRIMARY KEY, nomArticle TEXT, nomAuteur VARCHAR,infoSupplementaires TEXT)")
    curs.execute("DROP TABLE IF EXISTS AContribue")
    curs.execute("CREATE TABLE AContribue (nom VARCHAR,idArticle VARCHAR,PRIMARY KEY (nom,idArticle),FOREIGN KEY (idArticle) REFERENCES ARTICLE(idArticle),FOREIGN KEY (nom) REFERENCES PROF(nom))")
    conn.close()


def get_profs() -> list:
    """Récupère la liste des noms et prenoms des profs de la formation IDU et les ajoute à la base de données

    Returns:
        list: liste de profs
    """

    # se connecter à la base de données

    conn = sql.connect("polytechDatabase.db")
    curs = conn.cursor()

    # se connecter sur l'intranet

    f = open("login.txt", "r")
    login = [f.readline()[:-1], f.readline()]
    f.close()
    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-agent={USER_AGENT}")
    options.add_argument('--headless')
    driver = webdriver.Chrome(chrome_options=options)
    driver.get('https://www.polytech.univ-smb.fr/intranet/accueil.html')
    elem = driver.find_element(By.NAME, 'user')
    elem.clear()
    elem.send_keys(login[0])
    elem = driver.find_element(By.NAME, "pass")
    elem.clear()
    elem.send_keys(login[1])
    elem.send_keys(Keys.RETURN)

    # récuperer le lien vers toutes les matières

    driver.get(
        'https://www.polytech.univ-smb.fr/intranet/scolarite/programmes-ingenieur.html')

    # on s'intéresse uniquement aux IDU

    driver.find_element(
        By.XPATH, ('/html/body/div[2]/div/div/div/div[2]/div/div[5]/div[2]/div/div/form/ul/li[2]/div/input[11]')).click()

    # accéder aux matières via un clique

    scrolldown = driver.find_element(By.CSS_SELECTOR, 'div.titleBar')
    ActionChains(driver)\
        .scroll_to_element(scrolldown)\
        .perform()

    driver.find_element(By.CSS_SELECTOR, 'button.submit').click()
    tempo.sleep(5)

    # récupérer le nom de tous les professeurs en gérant certaines exceptions, je n'ai pas tout traitéhttps://www.binance.com/en/futures-activity/leaderboard/user?encryptedUid=FAD84AAFD6E43900BF15E06B21857715F

    matieres = driver.find_element(
        By.XPATH, '/html/body/div[2]/div/div/div/div[2]/div/div[5]/div[3]/div/div/div[2]')
    matieres = matieres.find_elements(By.CSS_SELECTOR, 'div.item')
    liste_enseignants = []
    for index_matiere in range(1, len(matieres)):
        driver.find_element(
            By.XPATH, f'/html/body/div[2]/div/div/div/div[2]/div/div[5]/div[3]/div/div/div[2]/div[{index_matiere}]/div[2]/ul/li[4]/a').click()
        new_enseignant = driver.find_element(
            By.XPATH, '/html/body/div[2]/div/div/div/div[2]/div/div[5]/div[3]/div/div/div[2]/div[3]/div[1]/div[2]').text.lower()
        if new_enseignant != '':
            try:
                if type(new_enseignant) != list:
                    separateur = new_enseignant.index(';')
                    new_enseignant = [
                        new_enseignant[:separateur], new_enseignant[separateur+1:]]
            except:
                pass
            try:
                if type(new_enseignant) != list:
                    separateur = new_enseignant.index('/')
                    new_enseignant = [
                        new_enseignant[:separateur], new_enseignant[separateur+1:]]
            except:
                pass
            try:
                if type(new_enseignant) != list:
                    separateur = new_enseignant.index('-')
                    new_enseignant = [
                        new_enseignant[:separateur], new_enseignant[separateur+1:]]
            except:
                pass
            try:
                if type(new_enseignant) != list:
                    separateur = new_enseignant.index(',')
                    new_enseignant = [
                        new_enseignant[:separateur], new_enseignant[separateur+1:]]
            except:
                pass
            if type(new_enseignant) != list:
                indice = 3
                trouve = 0
                while (trouve == 0 and indice != len(new_enseignant)):
                    if new_enseignant[indice-3] == ' ' and new_enseignant[indice-2] == 'e' and new_enseignant[indice-1] == 't' and new_enseignant[indice] == ' ':
                        new_enseignant = [
                            new_enseignant[:indice-3], new_enseignant[indice+1:]]
                        trouve = 1
                    indice += 1

            if type(new_enseignant) != list:
                new_enseignant = [new_enseignant]
            similitude = 0
            for enseignant in liste_enseignants:
                for new in new_enseignant:
                    if enseignant == new:
                        similitude += 1
            if similitude == 0:
                liste_enseignants += new_enseignant
                for prof in new_enseignant:
                    curs.execute("INSERT INTO Prof(nom) VALUES (?)",
                                 (prof,))
                    conn.commit()
        driver.back()
    conn.close()
    return liste_enseignants


def get_articles(professeur, tousArticles=[]) -> list:
    """Récupères tous les articles dans lesquelles apparaît le professeur et ajoute les articles dans la base de données

    Args:
        professeur (string): nom du professeur

    Returns:
        list: [{'nom de larticle': [], 'nom de/des auteurs': [],
                       'information supplémentaires': [], 'ID': []},...]
    """
    # se connecter à la base de données

    conn = sql.connect("polytechDatabase.db")
    curs = conn.cursor()

    # récuperer les articles

    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-agent={USER_AGENT}")
    options.add_argument('--headless')
    driver = webdriver.Chrome(chrome_options=options)
    driver.get('https://hal.science/')
    recherche = driver.find_element(
        By.XPATH, '/html/body/main/section[2]/form/div/div/div/input')
    recherche.clear
    recherche.send_keys(f"\"{professeur}\"")
    driver.find_element(
        By.XPATH, '/html/body/main/section[2]/form/div/div/div/button').click()
    try:
        no_article = driver.find_element(
            By.XPATH, '/html/body/main/section/section/div[2]/div').text
        if no_article == 'Pas de résultat':
            return tousArticles
    except:
        pass
    listes_articles = tousArticles[:]
    end = False
    numero_page = 1
    while end != True:
        articles = driver.find_element(
            By.XPATH, '/html/body/main/section/section[2]/table/tbody')
        articles = driver.find_elements(By.TAG_NAME, 'tr')
        for article_index in range(1, len(articles)):
            end = False
            article = dict()
            article['nom de larticle'] = (driver.find_element(
                By.XPATH, f'/html/body/main/section/section[2]/table/tbody/tr[{article_index}]/td[3]/a/h3').text)
            article['nom de/des auteurs'] = (driver.find_element(
                By.XPATH, f'/html/body/main/section/section[2]/table/tbody/tr[{article_index}]/td[3]/span[1]/a').text)
            article['information supplémentaires'] = (driver.find_element(
                By.XPATH, f'/html/body/main/section/section[2]/table/tbody/tr[{article_index}]/td[3]/div').text)
            article['ID'] = (driver.find_element(
                By.XPATH, f'/html/body/main/section/section[2]/table/tbody/tr[{article_index}]/td[3]/span[3]/a/strong').text)
            similitude = 0
            for unarticle in listes_articles:
                if unarticle == article:
                    similitude += 1
                    # on vérifie si on a déjà stocké la contribution de l'auteur dans la base de données
                    contribution = curs.execute(
                        f"SELECT nom FROM AContribue WHERE (nom='{professeur}' AND idArticle='{article['ID']}')")
                    if contribution == []:
                        curs.execute(
                            "INSERT INTO AContribue(nom,idArticle) VALUES (?,?)", (professeur, article["ID"]))
                        conn.commit()
            if similitude == 0:
                curs.execute("INSERT INTO Article(idArticle,nomArticle,nomAuteur,infoSupplementaires) VALUES (?,?,?,?)",
                             (article["ID"], article["nom de larticle"], article["nom de/des auteurs"], article["information supplémentaires"]))
                curs.execute(
                    "INSERT INTO AContribue(nom,idArticle) VALUES (?,?)", (professeur, article["ID"]))
                listes_articles += [article]
                conn.commit()
            icone = driver.find_elements(
                By.CLASS_NAME, 'icon-consulter.disabled.hal-icon')
        if len(icone) == 0:
            try:
                driver.find_elements(
                    By.CLASS_NAME, 'focus-round.next-prev.page-item')[1].click()
            except:
                end = True
        elif numero_page != 1:
            end = True
        else:
            try:
                driver.find_element(
                    By.CLASS_NAME, 'focus-round.next-prev.page-item').click()
            except:
                end = True
        numero_page += 1
    conn.close()
    return listes_articles


def get_cours(professeur):
    """fonction abandonnée pour se focaliser sur l'autre projet

    Args:
        professeur (_type_): nom du professeur
    """

    f = open("login.txt", "r")
    login = [f.readline()[:-1], f.readline()]
    f.close()
    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-agent={USER_AGENT}")
    # options.add_argument('--headless')
    driver = webdriver.Chrome(chrome_options=options)
    driver.get('https://www.polytech.univ-smb.fr/intranet/accueil.html')
    elem = driver.find_element(By.NAME, 'user')
    elem.clear()
    elem.send_keys(login[0])
    elem = driver.find_element(By.NAME, "pass")
    elem.clear
    elem.send_keys(login[1])
    elem.send_keys(Keys.RETURN)
    driver.get("https://www.univ-smb.fr/edt")
    elem = driver.find_element(By.NAME, 'username')
    elem.clear()
    elem.send_keys(login[0])
    elem = driver.find_element(By.NAME, "password")
    elem.clear
    elem.send_keys(login[1])
    elem.send_keys(Keys.RETURN)
    tempo.sleep(8)
    elem = driver.find_element(
        By.XPATH, '/html/body/div[1]/div[1]/div[2]/div[1]/div[2]/div[1]/div[1]/input')
    elem.send_keys(professeur)
    elem.send_keys(Keys.RETURN)
    # tempo.sleep(5)
    # elem = driver.find_element(
    #     By.XPATH, '/html/body/div[1]/div[1]/div[2]/div[2]/div[2]/div[1]/div/div[1]/div/div[2]/div[1]/div[2]/div/div[16]/table/tbody/tr/td[2]/div/div/div/img[3]')
    # j'arrive à obtenir des éléments mais je n'arrive pas à cliquer sur les éléments
    tempo.sleep(10)


if __name__ == '__main__':
    # fonctionnement normal
    creation_database()
    profs = get_profs()
    articles = []
    for prof in profs:
        print(prof)
        articles = get_articles(prof, articles)
