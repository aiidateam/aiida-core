#!/bin/bash

# Script: review-commits.sh
# Description:
#   Find and review commits since a tag, in a range, or untagged commits.
#   Opens PRs in browser for review using gh cli.
#
# Usage:
#   ./review-commits.sh <tag>              # Show commits since tag
#   ./review-commits.sh <range>            # Show commits in range (e.g., v2.7.1..HEAD)
#   ./review-commits.sh --untagged         # Show commits not in any tag
#   ./review-commits.sh <tag> --batch      # Open PRs in batches of 5
#
# Example:
#   ./review-commits.sh v2.7.1
#   ./review-commits.sh v2.7.1..HEAD
#   ./review-commits.sh v2.7.1..main
#   ./review-commits.sh --untagged --batch

set -e

GITHUB_REPO="aiidateam/aiida-core"
BATCH_MODE=false
BATCH_SIZE=5

# Parse options
while [[ $# -gt 0 ]]; do
    case $1 in
        --batch)
            BATCH_MODE=true
            shift
            ;;
        --untagged)
            MODE="untagged"
            shift
            ;;
        *)
            INPUT="$1"
            shift
            ;;
    esac
done

# Determine which commits to show
if [ "$MODE" = "untagged" ]; then
    echo "Finding commits not in any tag..."
    echo ""

    # Get all commits not reachable from any tag
    all_tagged_commits=$(git rev-list --no-walk --tags 2>/dev/null || echo "")

    if [ -z "$all_tagged_commits" ]; then
        echo "No tags found in repository."
        COMMITS=$(git log --pretty=format:"%h" --reverse HEAD)
    else
        # Get commits in HEAD that are not reachable from any tag
        COMMITS=$(git log --pretty=format:"%h" --reverse HEAD --not $(git rev-list --no-walk --tags))
    fi

    if [ -z "$COMMITS" ]; then
        echo "No untagged commits found."
        exit 0
    fi

    echo "Untagged commits:"

else
    if [ -z "$INPUT" ]; then
        echo "Usage: $0 <tag|range> [--batch]"
        echo "   or: $0 --untagged [--batch]"
        echo ""
        echo "Examples:"
        echo "  $0 v2.7.1              # Commits since tag"
        echo "  $0 v2.7.1..HEAD        # Commits in range"
        echo "  $0 v2.7.1..main        # Commits between tag and branch"
        echo "  $0 --untagged          # Commits not in any tag"
        exit 1
    fi

    # Check if input contains ".." (range syntax)
    if [[ "$INPUT" == *".."* ]]; then
        MODE="range"
        RANGE="$INPUT"

        echo "Finding commits in range $RANGE..."
        echo ""

        # Verify range is valid by checking if git log works with it
        if ! git log "$RANGE" --oneline -1 >/dev/null 2>&1; then
            echo "❌ Error: Invalid range '$RANGE'"
            exit 1
        fi

        COMMITS=$(git log "$RANGE" --pretty=format:"%h" --reverse)

        if [ -z "$COMMITS" ]; then
            echo "No commits found in range $RANGE"
            exit 0
        fi

        echo "Commits in $RANGE:"

    else
        MODE="since-tag"
        TAG="$INPUT"

        # Verify tag exists
        if ! git rev-parse --verify "$TAG" >/dev/null 2>&1; then
            echo "❌ Error: Tag '$TAG' not found"
            echo ""
            echo "Available tags:"
            git tag -l | tail -10
            exit 1
        fi

        echo "Finding commits since $TAG..."
        echo ""

        COMMITS=$(git log "$TAG"..HEAD --pretty=format:"%h" --reverse)

        if [ -z "$COMMITS" ]; then
            echo "No commits found since $TAG"
            exit 0
        fi

        echo "Commits since $TAG:"
    fi
fi

# Show the commits
echo ""
FIRST_COMMIT=$(echo "$COMMITS" | head -1)
LAST_COMMIT=$(echo "$COMMITS" | tail -1)

if [ "$FIRST_COMMIT" = "$LAST_COMMIT" ]; then
    git log --oneline -1 "$FIRST_COMMIT"
else
    git log --oneline --reverse "$FIRST_COMMIT"^.."$LAST_COMMIT"
fi

echo ""

# Count commits
COMMIT_COUNT=$(echo "$COMMITS" | wc -l)
echo "Total: $COMMIT_COUNT commits"
echo ""

# Extract PR numbers
if [ "$FIRST_COMMIT" = "$LAST_COMMIT" ]; then
    PR_NUMBERS=$(git log --oneline -1 "$FIRST_COMMIT" | grep -oP '#\K\d+' | sort -u)
else
    PR_NUMBERS=$(git log --oneline --reverse "$FIRST_COMMIT"^.."$LAST_COMMIT" | grep -oP '#\K\d+' | sort -u)
fi

if [ -z "$PR_NUMBERS" ]; then
    echo "No PRs found in these commits."
    echo ""
    echo "Commit hashes for cherry-picking:"
    echo "$COMMITS" | tr '\n' ' '
    echo ""
    exit 0
fi

PR_COUNT=$(echo "$PR_NUMBERS" | wc -l)
echo "Found $PR_COUNT unique PRs"
echo ""

# Ask if user wants to open PRs
if [ "$BATCH_MODE" = true ]; then
    echo "Opening PRs in batches of $BATCH_SIZE..."
    echo ""

    counter=0

    for pr in $PR_NUMBERS; do
        gh pr view "$pr" --web
        ((counter++))

        if [ $((counter % BATCH_SIZE)) -eq 0 ] && [ $counter -lt $PR_COUNT ]; then
            echo "Opened $counter/$PR_COUNT PRs"
            read -p "Press Enter to open next batch..." -r
            echo ""
        fi
    done

    remaining=$((counter % BATCH_SIZE))
    if [ $remaining -ne 0 ]; then
        echo "Opened final batch ($remaining PRs) - Total: $counter/$PR_COUNT"
    else
        echo "Opened all $PR_COUNT PRs"
    fi
else
    read -p "Open all $PR_COUNT PRs in browser? (y/N) " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Opening PRs..."
        for pr in $PR_NUMBERS; do
            gh pr view "$pr" --web
        done
        echo "✅ Opened $PR_COUNT PRs"
    fi
fi

echo ""
echo "=========================================="
echo "Commit hashes for cherry-picking:"
echo ""
echo "$COMMITS" | tr '\n' ' '
echo ""
echo ""
echo "To cherry-pick these commits, run:"
echo "./patch-release.sh $(echo $COMMITS | tr '\n' ' ')"
echo ""
