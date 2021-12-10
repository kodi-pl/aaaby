

# Submodules

Open source projects taken directly to this project.

- qualname, Wouter Bolsterlee, BSD, https://github.com/wbolster/qualname


# Sekcja polska

*This is section in Polish.*


## Założenia

### Założenia główne

- budowa pudełkowa (czyli modułowa) – zbiór łatwo używalnych części
- wspólny kodu – robimy małe moduły zamiast kopiowania czy ręcznie tego samego
- używamy dostępnych bibliotek, zamiast ręcznie robić to co już jest (jak np. zamiana `&ocute;`)
- działamy na Kodi 18 i 19 czyli w Py2 i Py3


## Założenia technicznie

- z powodu Py2/3 piszemy jeden kod (przynajmniej w przytłaczającej większości)
    - [compatible_idioms](https://python-future.org/compatible_idioms.html)
- używamy bibliotek do ujednolicania jak `future`, `six`, i dodatków jak [`kodi.six`](https://github.com/romanvm/kodi.six)
- w Py2 posiłkujemy się bogatym zestawem z `__future__` żeby nie walczyć z oczywistościami i kod mieć podobny do Py3, np.:  
```python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, unicode_literals, print_function
```
- czytamy [dokumentację Kodi](https://kodi.wiki/view/Category:Add-on_development),
    w tym [strukturę dodatku](https://kodi.wiki/view/Add-on_structure),
    a [opis API](https://codedocs.xyz/xbmc/xbmc/group__python.html) szczególnie!
- wszędzie gdzie się da używamy unicode (`str` po `from __future__ import unicode_literals`), a także `repoonse.text` zamiast `response.content` z `requests`

**Luźne uwagi** (w tym implementacja powyższego):

- zaprzyjaźniamy się z klasami
- przepraszamy się z dekoratorami
- kod w konwencji *NIX (sam `\n`)
- unittesty koniecznie
- jakiś cykl wydawniczy, szybkość jest piękna, ale nie kosztem jakości (w tym czytelności kodu)
- może przydadzą się [niektóre narzędzia](https://kodi.wiki/view/Development_Tools)
