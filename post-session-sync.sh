#!/bin/bash
#
# Post-Session Git Sync Script
# Run this AFTER finishing work on current OS
#
# Purpose: Commit all changes and push to remote repository
# Usage: ./post-session-sync.sh [optional commit message]
#

set -e  # Exit on error

echo "========================================="
echo "Post-Session Git Sync"
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
if git diff-index --quiet HEAD --; then
    echo "No uncommitted changes found."
    echo ""

    # Check if ahead of remote
    AHEAD=$(git rev-list origin/$CURRENT_BRANCH..HEAD --count 2>/dev/null || echo "0")
    if [ "$AHEAD" = "0" ]; then
        echo "Already synchronized with remote. Nothing to push."
        exit 0
    else
        echo "You have $AHEAD unpushed commits."
        echo ""
        read -p "Push to remote? (yes/no): " PUSH_CONFIRM
        if [ "$PUSH_CONFIRM" = "yes" ]; then
            git push origin $CURRENT_BRANCH
            echo "Pushed to remote successfully!"
        fi
        exit 0
    fi
fi

# Show what will be committed
echo "Changes to be committed:"
git status --short
echo ""

# Get commit message
if [ -n "$1" ]; then
    COMMIT_MSG="$1"
else
    echo "Enter commit message (or press Enter for auto-generated message):"
    read -p "> " COMMIT_MSG

    if [ -z "$COMMIT_MSG" ]; then
        # Auto-generate commit message
        OS_NAME=$(uname -s)
        SESSION_DATE=$(date +"%B %d, %Y")
        COMMIT_MSG="Session work on $OS_NAME - $SESSION_DATE"
    fi
fi

echo ""
echo "Commit message: $COMMIT_MSG"
echo ""

# Confirm
read -p "Stage and commit all changes? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Sync cancelled."
    exit 1
fi

# Stage all changes
echo "Staging all changes..."
git add -A
echo ""

# Create commit
echo "Creating commit..."
git commit -m "$COMMIT_MSG

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
echo ""

# Push to remote
echo "Pushing to remote..."
if git push origin $CURRENT_BRANCH; then
    echo ""
    echo "========================================="
    echo "Sync completed successfully!"
    echo "========================================="
    echo ""
    echo "All changes committed and pushed to remote."
    echo "Safe to switch to another OS."
    echo ""
else
    echo ""
    echo "ERROR: Push failed!"
    echo ""
    echo "Common causes:"
    echo "  - Network issue"
    echo "  - Remote has newer commits (run pre-session-sync.sh first)"
    echo "  - Authentication issue"
    echo ""
    echo "Your changes are committed locally."
    echo "You can try pushing again later with:"
    echo "  git push origin $CURRENT_BRANCH"
    exit 1
fi
