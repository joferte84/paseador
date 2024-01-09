from caracter_perro import caracteristicas_perros

def estimar_velocidad(raza):
    # Obtener el perfil de la raza del perro
    perfil_raza = caracteristicas_perros.get(raza, {"Comportamiento": "Desconocido", "Tamaño": "Mediano"})

    # Obtener el comportamiento de la raza del perro
    comportamiento = perfil_raza["Comportamiento"].lower()

    # Velocidades ajustadas para los tres comportamientos
    if comportamiento == 'tranquilo':
        return 2  # Velocidad más lenta para perros tranquilos
    elif comportamiento == 'curioso':
        return 3  # Velocidad media
    elif comportamiento == 'energético':
        return 4  # Velocidad más alta para perros energéticos

    return 3  # Velocidad por defecto si no hay suficiente información

def estimar_distancia(duracion, perfil_perro):
    # Obtiene la raza del perro desde el perfil
    raza = perfil_perro.get('raza')
    # Calcula la velocidad basada en la raza del perro
    velocidad = estimar_velocidad(raza)
    # Calcula la distancia basada en la duración del paseo y la velocidad
    return duracion * velocidad

