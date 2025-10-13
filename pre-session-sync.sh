#!/bin/bash
#
# Pre-Session Git Sync Script
# Run this BEFORE starting work on a different OS
#
# Purpose: Safely pull latest changes from remote repository
# Usage: ./pre-session-sync.sh
#

set -e  # Exit on error

echo "========================================="
echo "Pre-Session Git Sync"
echo "========================================="
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "ERROR: Not in a git repository"
    exit 1
fi

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"
echo ""

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "WARNING: You have uncommitted changes!"
    echo ""
    git status --short
    echo ""
    echo "Options:"
    echo "  1. Commit changes first (recommended)"
    echo "  2. Stash changes (git stash)"
    echo "  3. Discard changes (git reset --hard HEAD)"
    echo ""
    read -p "Do you want to continue anyway? (yes/no): " CONTINUE
    if [ "$CONTINUE" != "yes" ]; then
        echo "Aborting. Please handle uncommitted changes first."
        exit 1
    fi
fi

# Fetch latest from remote
echo "Fetching latest changes from remote..."
git fetch origin
echo ""

# Check what will be pulled
BEHIND=$(git rev-list HEAD..origin/$CURRENT_BRANCH --count 2>/dev/null || echo "0")
AHEAD=$(git rev-list origin/$CURRENT_BRANCH..HEAD --count 2>/dev/null || echo "0")

echo "Repository status:"
echo "  Commits behind remote: $BEHIND"
echo "  Commits ahead of remote: $AHEAD"
echo ""

if [ "$BEHIND" = "0" ]; then
    echo "Already up to date! No sync needed."
    exit 0
fi

# Show what will be pulled
echo "Commits to be pulled:"
git log HEAD..origin/$CURRENT_BRANCH --oneline --decorate
echo ""

# Ask for confirmation
read -p "Pull these changes? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Sync cancelled."
    exit 1
fi

# Create backup branch
BACKUP_BRANCH="backup-before-sync-$(date +%Y%m%d-%H%M%S)"
echo ""
echo "Creating backup branch: $BACKUP_BRANCH"
git checkout -b $BACKUP_BRANCH
git checkout $CURRENT_BRANCH
echo ""

# Pull with rebase
echo "Pulling changes with rebase strategy..."
if git pull --rebase origin $CURRENT_BRANCH; then
    echo ""
    echo "========================================="
    echo "Sync completed successfully!"
    echo "========================================="
    echo ""
    echo "Backup branch created: $BACKUP_BRANCH"
    echo ""
    echo "If something went wrong, restore with:"
    echo "  git checkout $BACKUP_BRANCH"
    echo ""
else
    echo ""
    echo "ERROR: Sync failed!"
    echo ""
    echo "To restore backup:"
    echo "  git rebase --abort"
    echo "  git checkout $BACKUP_BRANCH"
    exit 1
fi
