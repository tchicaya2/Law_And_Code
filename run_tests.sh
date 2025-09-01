#!/bin/bash

# Script d'exécution des tests
# Usage: ./run_tests.sh [option]

set -e  # Arrêter en cas d'erreur

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction d'affichage
print_header() {
    echo -e "${BLUE}===================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}===================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Vérifier que pytest est installé
check_pytest() {
    if ! command -v pytest &> /dev/null; then
        print_error "pytest n'est pas installé"
        echo "Installation: pip install pytest pytest-cov"
        exit 1
    fi
}

# Configuration de l'environnement Python
setup_python_env() {
    print_header "Configuration de l'environnement Python"
    
    # Vérifier Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 n'est pas disponible"
        exit 1
    fi
    
    # Vérifier les dépendances
    python3 -c "import flask, pytest" 2>/dev/null || {
        print_warning "Installation des dépendances requises..."
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-xdist
    }
    
    print_success "Environnement Python configuré"
}

# Tests unitaires rapides
run_unit_tests() {
    print_header "Exécution des Tests Unitaires"
    pytest tests/test_helpers.py tests/test_auth.py -v --tb=short
    print_success "Tests unitaires terminés"
}

# Tests d'intégration
run_integration_tests() {
    print_header "Exécution des Tests d'Intégration"
    pytest tests/test_integration.py tests/test_quiz.py tests/test_main.py --run-integration -v
    print_success "Tests d'intégration terminés"
}

# Tests de performance
run_performance_tests() {
    print_header "Exécution des Tests de Performance"
    pytest -m slow --run-slow -v
    print_success "Tests de performance terminés"
}

# Tous les tests
run_all_tests() {
    print_header "Exécution de Tous les Tests"
    pytest --run-integration --run-slow -v
    print_success "Tous les tests terminés"
}

# Tests avec couverture
run_coverage_tests() {
    print_header "Tests avec Couverture de Code"
    pytest --cov=helpers --cov=app --cov-report=html --cov-report=term-missing -v
    print_success "Tests avec couverture terminés"
    print_warning "Rapport HTML généré dans htmlcov/"
}

# Tests parallèles
run_parallel_tests() {
    print_header "Tests en Parallèle"
    if command -v pytest-xdist &> /dev/null; then
        pytest -n auto -v
        print_success "Tests parallèles terminés"
    else
        print_warning "pytest-xdist non installé, exécution séquentielle"
        pytest -v
    fi
}

# Tests par catégorie
run_category_tests() {
    local category=$1
    print_header "Tests de Catégorie: $category"
    
    case $category in
        "auth")
            pytest -m auth -v
            ;;
        "cache")
            pytest -m cache -v
            ;;
        "db")
            pytest -m db -v
            ;;
        *)
            print_error "Catégorie inconnue: $category"
            echo "Catégories disponibles: auth, cache, db"
            exit 1
            ;;
    esac
    
    print_success "Tests de catégorie '$category' terminés"
}

# Nettoyage
cleanup() {
    print_header "Nettoyage"
    
    # Supprimer les fichiers de cache
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    
    # Nettoyer les fichiers de session de test
    rm -rf flask_session_test 2>/dev/null || true
    
    # Nettoyer les logs de test
    rm -f test.log 2>/dev/null || true
    
    print_success "Nettoyage terminé"
}

# Validation pré-tests
pre_test_validation() {
    print_header "Validation Pré-Tests"
    
    # Vérifier la structure des fichiers
    required_files=(
        "tests/conftest.py"
        "tests/test_helpers.py"
        "tests/test_auth.py"
        "tests/test_quiz.py"
        "tests/test_main.py"
        "tests/test_integration.py"
    )
    
    for file in "${required_files[@]}"; do
        if [[ -f "$file" ]]; then
            print_success "Fichier trouvé: $file"
        else
            print_error "Fichier manquant: $file"
            exit 1
        fi
    done
    
    # Vérifier la syntaxe Python
    python3 -m py_compile tests/*.py
    print_success "Syntaxe Python validée"
}

# Rapport de test
generate_report() {
    print_header "Génération du Rapport de Test"
    
    # Exécuter les tests avec rapport détaillé
    pytest --html=test_report.html --self-contained-html --cov=helpers --cov=app --cov-report=html
    
    print_success "Rapport HTML généré: test_report.html"
    print_success "Couverture HTML générée: htmlcov/index.html"
}

# Mode CI/CD
run_ci_tests() {
    print_header "Mode CI/CD"
    
    # Tests essentiels pour CI/CD
    pytest tests/test_helpers.py tests/test_auth.py -v --tb=short || exit 1
    pytest tests/test_quiz.py tests/test_main.py --run-integration -v || exit 1
    
    # Couverture minimale requise
    pytest --cov=helpers --cov=app --cov-fail-under=70
    
    print_success "Tests CI/CD réussis"
}

# Affichage de l'aide
show_help() {
    echo "Usage: $0 [option]"
    echo ""
    echo "Options:"
    echo "  unit          Tests unitaires rapides"
    echo "  integration   Tests d'intégration"
    echo "  performance   Tests de performance"
    echo "  all           Tous les tests"
    echo "  coverage      Tests avec couverture"
    echo "  parallel      Tests en parallèle"
    echo "  category      Tests par catégorie (auth|cache|db)"
    echo "  cleanup       Nettoyage des fichiers temporaires"
    echo "  validate      Validation pré-tests"
    echo "  report        Génération de rapport HTML"
    echo "  ci            Mode CI/CD"
    echo "  help          Afficher cette aide"
    echo ""
    echo "Exemples:"
    echo "  $0 unit"
    echo "  $0 coverage"
    echo "  $0 category auth"
}

# Main
main() {
    # Vérifications initiales
    check_pytest
    
    case "${1:-help}" in
        "unit")
            setup_python_env
            pre_test_validation
            run_unit_tests
            ;;
        "integration")
            setup_python_env
            pre_test_validation
            run_integration_tests
            ;;
        "performance")
            setup_python_env
            pre_test_validation
            run_performance_tests
            ;;
        "all")
            setup_python_env
            pre_test_validation
            run_all_tests
            ;;
        "coverage")
            setup_python_env
            pre_test_validation
            run_coverage_tests
            ;;
        "parallel")
            setup_python_env
            pre_test_validation
            run_parallel_tests
            ;;
        "category")
            if [[ -z "$2" ]]; then
                print_error "Catégorie requise"
                echo "Usage: $0 category [auth|cache|db]"
                exit 1
            fi
            setup_python_env
            pre_test_validation
            run_category_tests "$2"
            ;;
        "cleanup")
            cleanup
            ;;
        "validate")
            setup_python_env
            pre_test_validation
            ;;
        "report")
            setup_python_env
            pre_test_validation
            generate_report
            ;;
        "ci")
            setup_python_env
            run_ci_tests
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Point d'entrée
main "$@"
