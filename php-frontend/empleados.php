<?php
require_once 'config.php';
requireLogin();

$pdo = getDB();
$mensaje = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['crear'])) {
    try {
        $empresa = $pdo->query("SELECT id FROM empresas LIMIT 1")->fetch();
        $stmt = $pdo->prepare("INSERT INTO empleados (empresa_id, numero_empleado, nombre, apellido_paterno, apellido_materno, email, puesto) VALUES (?, ?, ?, ?, ?, ?, ?)");
        $stmt->execute([$empresa['id'], $_POST['numero_empleado'], $_POST['nombre'], $_POST['apellido_paterno'], $_POST['apellido_materno'], $_POST['email'], $_POST['puesto']]);
        $mensaje = '<div class="alert alert-success">Empleado creado</div>';
    } catch (Exception $e) {
        $mensaje = '<div class="alert alert-danger">Error: ' . $e->getMessage() . '</div>';
    }
}

$empleados = $pdo->query("SELECT e.*, (SELECT COUNT(*) FROM datos_biometricos WHERE empleado_id = e.id AND activo = true) as tiene_bio FROM empleados e WHERE e.activo = true ORDER BY e.apellido_paterno")->fetchAll();
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Empleados</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <nav class="navbar navbar-dark bg-primary"><div class="container"><a href="index.php" class="navbar-brand">Sistema Biometrico</a></div></nav>
    <div class="container py-4">
        <div class="d-flex justify-content-between mb-4">
            <h4>Empleados</h4>
            <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#modalNuevo">+ Nuevo</button>
        </div>
        <?= $mensaje ?>
        <div class="card"><div class="card-body">
            <table class="table">
                <thead><tr><th>No.</th><th>Nombre</th><th>Puesto</th><th>Biometrico</th><th>Acciones</th></tr></thead>
                <tbody>
                <?php foreach ($empleados as $e): ?>
                <tr>
                    <td><?= htmlspecialchars($e['numero_empleado']) ?></td>
                    <td><?= htmlspecialchars($e['nombre'] . ' ' . $e['apellido_paterno']) ?></td>
                    <td><?= htmlspecialchars($e['puesto']) ?></td>
                    <td><?= $e['tiene_bio'] > 0 ? '<span class="badge bg-success">OK</span>' : '<span class="badge bg-warning">Pendiente</span>' ?></td>
                    <td><a href="registrar_biometrico.php?id=<?= $e['id'] ?>" class="btn btn-sm btn-success">Registrar Rostro</a></td>
                </tr>
                <?php endforeach; ?>
                </tbody>
            </table>
        </div></div>
    </div>
    <div class="modal fade" id="modalNuevo" tabindex="-1"><div class="modal-dialog"><div class="modal-content">
        <form method="POST">
            <div class="modal-header"><h5>Nuevo Empleado</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
            <div class="modal-body">
                <div class="mb-3"><label>No. Empleado *</label><input type="text" name="numero_empleado" class="form-control" required></div>
                <div class="mb-3"><label>Nombre *</label><input type="text" name="nombre" class="form-control" required></div>
                <div class="mb-3"><label>Apellido Paterno *</label><input type="text" name="apellido_paterno" class="form-control" required></div>
                <div class="mb-3"><label>Apellido Materno</label><input type="text" name="apellido_materno" class="form-control"></div>
                <div class="mb-3"><label>Email</label><input type="email" name="email" class="form-control"></div>
                <div class="mb-3"><label>Puesto</label><input type="text" name="puesto" class="form-control"></div>
            </div>
            <div class="modal-footer"><button type="submit" name="crear" class="btn btn-primary">Guardar</button></div>
        </form>
    </div></div></div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
