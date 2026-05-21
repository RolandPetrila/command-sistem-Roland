"""
Modul Time Tracking — cronometru si evidenta timp lucrat, legat de facturare.

Endpoints:
  POST   /api/time/start           — porneste cronometru
  POST   /api/time/stop            — opreste cronometru activ
  GET    /api/time/active          — timer-ul activ curent
  GET    /api/time/entries         — lista inregistrari cu filtre
  POST   /api/time/entries         — inregistrare manuala
  PUT    /api/time/entries/{id}    — actualizare inregistrare
  DELETE /api/time/entries/{id}    — stergere inregistrare
  GET    /api/time/stats           — sumar ore azi/saptamana/luna + top proiecte/clienti
  GET    /api/time/stats/daily     — ore pe zi, ultimele 30 zile
  POST   /api/time/to-invoice-items — conversie inregistrari in articole factura
  POST   /api/time/mark-invoiced  — marcare inregistrari ca facturate
"""

from .router import router as time_router

MODULE_INFO = {
    "name": "timetracking",
    "description": "Cronometru si time tracking legat de facturare",
    "routers": [time_router],
    "category": "Productivitate",
    "icon": "Clock",
    "order": 18,
}
