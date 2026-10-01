# ════════════════════════════════════════════════════════════════════════════════
# PANEL DE MÉTRICAS CLAVE - VERSIÓN MEJORADA
# ════════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.header("📊 Panel de Métricas Clave")
st.markdown("**Estado financiero y operativo del consorcio en tiempo real**")

resultado_contable = resultados.get(TipoAgente.CONTABLE.value)
resultado_mora = resultados.get(TipoAgente.MORA.value)

if resultado_contable and resultado_contable.estado == EstadoAgente.COMPLETADO:
    datos_contables = resultado_contable.datos_procesados
    edificio_data = ESTADISTICAS_EDIFICIOS[edificio_seleccionado]
    
    # FILA 1: SALUD FINANCIERA
    st.subheader("💰 Salud Financiera")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "💵 Ingresos Totales",
            f"${datos_contables['total_ingresos']:,.0f}",
            delta="Periodo actual"
        )
    
    with col2:
        st.metric(
            "💸 Gastos Totales",
            f"${datos_contables['total_gastos']:,.0f}",
            delta=f"{(datos_contables['total_gastos']/datos_contables['total_ingresos']*100):.1f}% de ingresos"
        )
    
    with col3:
        balance = datos_contables['balance_neto']
        delta_color = "Superávit ✅" if balance > 0 else "Déficit ❌"
        st.metric(
            "⚖️ Balance Neto",
            f"${balance:,.0f}",
            delta=delta_color
        )
    
    with col4:
        porcentaje_utlidad = (balance / datos_contables['total_ingresos'] * 100) if datos_contables['total_ingresos'] > 0 else 0
        st.metric(
            "📈 Margen",
            f"{porcentaje_utlidad:.1f}%",
            delta="De la facturación"
        )
    
    with col5:
        st.metric(
            "🏦 Fondos de Reserva",
            f"${edificio_data['reserva']:,.0f}",
            delta="Fondo de contingencia"
        )
    
    st.markdown("---")
    
    # FILA 2: MOROSIDAD Y RIESGOS
    st.subheader("⚠️ Gestión de Riesgos")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        resultado_mora = resultados.get(TipoAgente.MORA.value)
        mora_txt = resultado_mora.datos_procesados.get("uf_en_mora", 0) if resultado_mora else 0
        
        if mora_txt > 2:
            estado_mora = "🔴 CRÍTICO"
            delta_mora = "Acción inmediata"
        elif mora_txt > 0:
            estado_mora = "🟡 MODERADO"
            delta_mora = "Seguimiento"
        else:
            estado_mora = "🟢 CONTROLADO"
            delta_mora = "Sin problemas"
        
        st.metric(
            "⚠️ UF en Mora",
            mora_txt,
            delta=delta_mora
        )
    
    with col2:
        # Proyectar cobranza pendiente
        cobranza_pendiente = datos_contables['total_gastos'] * 0.15  # Asumimos 15% pendiente
        st.metric(
            "💳 Cobranza Pendiente",
            f"${cobranza_pendiente:,.0f}",
            delta="Estimado a recuperar"
        )
    
    with col3:
        # Tasa de morosidad
        tasa_morosidad = (mora_txt / 50) * 100 if mora_txt > 0 else 0  # Asumimos 50 UF
        st.metric(
            "📊 Tasa Morosidad",
            f"{tasa_morosidad:.1f}%",
            delta="Del total de UF"
        )
    
    with col4:
        # Días de gastos en caja (liquidity ratio)
        dias_caja = (edificio_data['reserva'] / datos_contables['total_gastos'] * 30) if datos_contables['total_gastos'] > 0 else 0
        st.metric(
            "📅 Días de Caja",
            f"{dias_caja:.0f} días",
            delta="Capacidad de solvencia"
        )
    
    with col5:
        # Índice de eficiencia (Gastos/Ingresos)
        indice_eficiencia = (datos_contables['total_gastos'] / datos_contables['total_ingresos'] * 100) if datos_contables['total_ingresos'] > 0 else 0
        if indice_eficiencia < 80:
            eficiencia = "✅ Excelente"
        elif indice_eficiencia < 90:
            eficiencia = "🟢 Buena"
        elif indice_eficiencia < 100:
            eficiencia = "🟡 Aceptable"
        else:
            eficiencia = "🔴 Deficitaria"
        
        st.metric(
            "🎯 Eficiencia",
            f"{indice_eficiencia:.1f}%",
            delta=eficiencia
        )
    
    st.markdown("---")
    
    # FILA 3: COMPOSICIÓN DE GASTOS
    st.subheader("📋 Desglose de Gastos")
    col1, col2, col3, col4 = st.columns(4)
    
    # Calcular porcentajes de gastos
    gastos_df = pd.DataFrame(resultado_contable.datos_procesados["gastos"])
    total_gastos = gastos_df["Monto ($)"].sum()
    
    gastos_ordenados = gastos_df.nlargest(4, "Monto ($)")
    
    for idx, (col, gasto_row) in enumerate(zip([col1, col2, col3, col4], gastos_ordenados.iterrows())):
        with col:
            gasto = gasto_row[1]
            porcentaje = (gasto["Monto ($)"] / total_gastos * 100) if total_gastos > 0 else 0
            
            # Asignar emoji según tipo
            if "reparación" in gasto["Gastos"].lower():
                emoji = "🔧"
            elif "honorario" in gasto["Gastos"].lower():
                emoji = "👔"
            elif "sueldo" in gasto["Gastos"].lower():
                emoji = "👨"
            elif "limpieza" in gasto["Gastos"].lower():
                emoji = "🧹"
            elif "luz" in gasto["Gastos"].lower():
                emoji = "💡"
            else:
                emoji = "📌"
            
            st.metric(
                f"{emoji} {gasto['Gastos'].title()}",
                f"${gasto['Monto ($)']:,.0f}",
                delta=f"{porcentaje:.1f}% del total"
            )
    
    st.markdown("---")
    
    # FILA 4: INDICADORES OPERATIVOS
    st.subheader("🔧 Indicadores Operativos")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "🏢 Edificios Gestionados",
            len(ESTADISTICAS_EDIFICIOS),
            delta="En cartera"
        )
    
    with col2:
        total_uf = sum([v.get("cantidad_uf", 0) for v in ESTADISTICAS_EDIFICIOS.values()])
        st.metric(
            "🏠 Unidades Funcionales",
            total_uf,
            delta="Total del portafolio"
        )
    
    with col3:
        st.metric(
            "👷 Proveedores Activos",
            len(DATOS_CARTILLA_PROVEEDORES),
            delta="Homologados"
        )
    
    with col4:
        st.metric(
            "📋 Órdenes de Trabajo",
            len(TABLA_SOLICITADA_OT),
            delta="En circulación"
        )
    
    st.markdown("---")
    
    # ALERTAS Y RECOMENDACIONES
    st.subheader("🚨 Alertas y Recomendaciones")
    
    alertas = []
    
    # Alerta 1: Morosidad
    if mora_txt > 2:
        alertas.append({
            "tipo": "🔴 CRÍTICO",
            "titulo": "Alta Morosidad Detectada",
            "descripcion": f"Hay {mora_txt} unidades en mora. Se recomienda acción legal inmediata.",
            "color": "error"
        })
    elif mora_txt > 0:
        alertas.append({
            "tipo": "🟡 MODERADO",
            "titulo": "Morosidad en Control",
            "descripcion": f"{mora_txt} UF en mora. Realizar seguimiento de cobranza.",
            "color": "warning"
        })
    
    # Alerta 2: Déficit
    if balance < 0:
        alertas.append({
            "tipo": "🔴 CRÍTICO",
            "titulo": "Consorcio Deficitario",
            "descripcion": f"Déficit de ${abs(balance):,.0f}. Revisar presupuesto.",
            "color": "error"
        })
    
    # Alerta 3: Baja Liquidez
    if dias_caja < 30:
        alertas.append({
            "tipo": "🟡 MODERADO",
            "titulo": "Baja Liquidez",
            "descripcion": f"Solo {dias_caja:.0f} días de caja. Considerar aumento de expensas.",
            "color": "warning"
        })
    
    # Alerta 4: Gastos Altos
    if indice_eficiencia > 95:
        alertas.append({
            "tipo": "🟡 MODERADO",
            "titulo": "Gastos Muy Altos",
            "descripcion": f"Gastos son {indice_eficiencia:.0f}% de ingresos. Requiere optimización.",
            "color": "warning"
        })
    
    # Mostrar alertas
    if alertas:
        for alerta in alertas:
            if alerta["color"] == "error":
                st.error(f"**{alerta['tipo']} - {alerta['titulo']}**\n{alerta['descripcion']}")
            else:
                st.warning(f"**{alerta['tipo']} - {alerta['titulo']}**\n{alerta['descripcion']}")
    else:
        st.success("✅ **Todo en orden** - No hay alertas críticas")
    
    st.markdown("---")
    
    # ÚLTIMA FILA: INFORMACIÓN DEL EDIFICIO SELECCIONADO
    st.subheader(f"📍 Información del Edificio: {edificio_seleccionado}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📊 Factor de Ocupación",
            f"{edificio_data['factor']:.2f}",
            delta="Ratios de ocupación"
        )
    
    with col2:
        st.metric(
            "📈 Tasa Vigente",
            f"{edificio_data['tasa']:.1f}%",
            delta="Interés anual"
        )
    
    with col3:
        st.metric(
            "🔧 Órdenes Activas",
            edificio_data['ots'],
            delta="En el edificio"
        )
    
    with col4:
        st.metric(
            "🏠 Unidades",
            edificio_data['cantidad_uf'],
            delta="Total de UF"
        )
