<?php
require_once 'config.php';
requireLogin();

$pdo = getDB();
$today = date('Y-m-d');

// Estadísticas
$totalEmpleados = $pdo->query("SELECT COUNT(*) FROM empleados WHERE activo = true")->fetchColumn();
$conBiometrico = $pdo->query("SELECT COUNT(DISTINCT empleado_id) FROM datos_biometricos WHERE activo = true")->fetchColumn();
$registrosHoy = $pdo->query("SELECT COUNT(*) FROM registros_asistencia WHERE fecha = CURRENT_DATE")->fetchColumn();

// Últimos registros
$stmt = $pdo->query("
    SELECT r.*, e.nombre, e.apellido_paterno 
    FROM registros_asistencia r
    JOIN empleados e ON r.empleado_id = e.id
    WHERE r.fecha = CURRENT_DATE
    ORDER BY r.timestamp_registro DESC
    LIMIT 10
");
$registros = $stmt->fetchAll();
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - Sistema Biométrico</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css" rel="stylesheet">
</head>
<body class="bg-light">
    <nav class="navbar navbar-dark bg-primary">
        <div class="container">
            <span class="navbar-brand">🏢 Sistema Biométrico</span>
            <span class="text-white">
                <?= sanitize($_SESSION['username']) ?> |
                <a href="logout.php" class="text-white">Salir</a>
            </span>
        </div>
    </nav>
    
    <div class="container py-4">
        <div class="row mb-4">
            <div class="col-md-4">
                <div class="card text-center">
                    <div class="card-body">
                        <h2 class="text-primary"><?= $totalEmpleados ?></h2>
                        <p class="mb-0">Empleados</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card text-center">
                    <div class="card-body">
                        <h2 class="text-success"><?= $conBiometrico ?></h2>
                        <p class="mb-0">Con Biométrico</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card text-center">
                    <div class="card-body">
                        <h2 class="text-info"><?= $registrosHoy ?></h2>
                        <p class="mb-0">Registros Hoy</p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mb-4">
            <div class="col">
                <a href="empleados.php" class="btn btn-primary me-2">
                    <i class="bi bi-people"></i> Empleados
                </a>
                <a href="registrar_biometrico.php" class="btn btn-success">
                    <i class="bi bi-fingerprint"></i> Registrar Biométrico
                </a>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <h5 class="mb-0">📋 Registros de Hoy</h5>
            </div>
            <div class="card-body">
                <?php if (empty($registros)): ?>
                    <p class="text-muted text-center py-4">No hay registros hoy</p>
                <?php else: ?>
                <table class="table">
                    <thead>
                        <tr>
                            <th>Empleado</th>
                            <th>Tipo</th>
                            <th>Hora</th>
                            <th>Confianza</th>
                            <th>Ubicación</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($registros as $r): ?>
                        <tr>
                            <td><?= sanitize($r['nombre'] . ' ' . $r['apellido_paterno']) ?></td>
                            <td>
                                <span class="badge bg-<?= $r['tipo'] == 'entrada' ? 'success' : 'danger' ?>">
                                    <?= ucfirst($r['tipo']) ?>
                                </span>
                            </td>
                            <td><?= substr($r['hora'], 0, 5) ?></td>
                            <td><?= $r['confianza_match'] ?>%</td>
                            <td>
                                <?= $r['dentro_rango'] ? '✅ En rango' : '⚠️ Fuera' ?>
                            </td>
                        </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
                <?php endif; ?>
            </div>
        </div>
    </div>
</body>
</html>
