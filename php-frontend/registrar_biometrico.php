'✅';
                document.getElementById('resultTitle').innerHTML = 'Registrado!';
                document.getElementById('resultMsg').innerHTML = 'Calidad: ' + (data.calidad || '--') + '%';
            } else {
                document.getElementById('resultIcon').innerHTML = '❌';
                document.getElementById('resultTitle').innerHTML = 'Error';
                document.getElementById('resultMsg').innerHTML = data.message;
            }
        } catch(e) {
            alert('Error: ' + e);
        }
    };
    </script>
</body>
</html>
