package com.example.data

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "missions")
data class Mission(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val time: String,
    val title: String,
    val isCompleted: Boolean = false,
    val category: String = "GENERAL",
    val timestamp: Long = System.currentTimeMillis()
)

@Entity(tableName = "action_logs")
data class ActionLogEntry(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val timestamp: String,
    val source: String, // e.g. "SYSTEM", "CAMERA_1", "AI_CORE", "COMMAND", "SYNC", "MCP", "OBSBOT"
    val message: String,
    val logType: String = "INFO" // "INFO", "SUCCESS", "WARNING", "ERROR"
)

@Entity(tableName = "obsidian_notes")
data class ObsidianNote(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val title: String,
    val path: String,
    val content: String,
    val isProtected: Boolean = false, // OverwriteError protection for Charter.md, ADRs
    val updatedAt: Long = System.currentTimeMillis()
)
