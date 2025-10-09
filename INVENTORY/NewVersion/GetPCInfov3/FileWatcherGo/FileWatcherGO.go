package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
	"os/signal"
	"path/filepath"
	"strings"
	"syscall"
	"time"

	"github.com/fsnotify/fsnotify"
	"github.com/joho/godotenv"
	_ "github.com/mattn/go-sqlite3"
)

// DebugMode enables debug logging
const DebugMode = false

// Config holds the application configuration
type Config struct {
	WProgram    string
	FilePath    string
	DBName      string
	JSPath      string
	JSData      string
	SQLiteTable string
}

// Query represents a query from queries.json
type Query struct {
	Query   string `json:"query"`
	JSFile  string `json:"jsfile"`
}

// Record represents a row from the SQLite database
type Record map[string]interface{}

// SQLiteExtractor manages the extraction process
type SQLiteExtractor struct {
	config        Config
	watcher       *fsnotify.Watcher
	isListening   bool
	running       bool
	lastDBModified float64
}

// NewSQLiteExtractor initializes a new extractor
func NewSQLiteExtractor() (*SQLiteExtractor, error) {
	extractor := &SQLiteExtractor{
		running: true,
	}
	if err := extractor.loadEnvConfig(); err != nil {
		return nil, err
	}
	return extractor, nil
}

// logMessage prints a message with timestamp
func (e *SQLiteExtractor) logMessage(message string) {
	fmt.Printf("%s - %s\n", time.Now().Format("15:04:05"), message)
}

// debugPrint prints message if debug mode is enabled
func debugPrint(message string) {
	if DebugMode {
		fmt.Println(message)
	}
}

// loadEnvConfig loads configuration from .env file
func (e *SQLiteExtractor) loadEnvConfig() error {
	if _, err := os.Stat(".env"); os.IsNotExist(err) {
		e.logMessage("⚠️ No .env file found")
		return nil
	}
	if err := godotenv.Load(); err != nil {
		e.logMessage(fmt.Sprintf("❌ Error loading .env: %v", err))
		return err
	}
	e.config = Config{
		WProgram:    os.Getenv("WPROGRAM"),
		FilePath:    os.Getenv("FILE_PATH"),
		DBName:      os.Getenv("FILE_SQLITE"),
		JSPath:      os.Getenv("JS_PATH"),
		JSData:      os.Getenv("JS_DATA"),
		SQLiteTable: os.Getenv("SQLITETABLE"),
	}
	if e.config.WProgram == "" {
		e.config.WProgram = "Unknown"
	}
	if e.config.JSData == "" {
		e.config.JSData = "DataIn.js"
	}
	e.logMessage(fmt.Sprintf("✅ Loaded .env configuration: %s", e.config.WProgram))
	return nil
}

// extractAndSave performs data extraction and saves to JavaScript files
func (e *SQLiteExtractor) extractAndSave() {
	e.logMessage("Processing SQLite Extraction...")
	dbPath := filepath.Join(e.config.FilePath, e.config.DBName+".db")
	queryFile := filepath.Join(e.config.FilePath, "queries.json")

	if _, err := os.Stat(queryFile); os.IsNotExist(err) {
		e.logMessage(fmt.Sprintf("⚠️ Query file not found: %s, using default query", queryFile))
		jsFilePath := filepath.Join(e.config.JSPath, e.config.JSData)
		sqlQuery := fmt.Sprintf("SELECT * FROM %s", e.config.SQLiteTable)
		e.logMessage("🚀 Starting extraction for default query")
		data, err := e.extractTableData(dbPath, e.config.SQLiteTable, sqlQuery)
		if err != nil || len(data) == 0 {
			e.logMessage("⚠️ No data extracted for default query")
			return
		}
		e.logMessage("🔄 Processing data for default query...")
		processed := e.processData(data)
		e.logMessage(fmt.Sprintf("👍👍👍 Saving to %s...", e.config.JSData))
		if err := e.saveToJS(processed, jsFilePath, "default query"); err != nil {
			return
		}
		return
	}

	file, err := os.Open(queryFile)
	if err != nil {
		e.logMessage(fmt.Sprintf("❌ Error reading query file: %v", err))
		return
	}
	defer file.Close()

	var jsonData struct {
		Queries map[string]Query `json:"queries"`
	}
	if err := json.NewDecoder(file).Decode(&jsonData); err != nil {
		e.logMessage(fmt.Sprintf("❌ Error parsing query file: %v", err))
		return
	}

	if len(jsonData.Queries) == 0 {
		e.logMessage("⚠️ No queries found in JSON file")
		return
	}

	for queryKey, queryInfo := range jsonData.Queries {
		if !e.running {
			e.logMessage("🛑 Extraction stopped")
			break
		}
		if queryInfo.Query == "" {
			e.logMessage(fmt.Sprintf("❌ No query found for key: %s", queryKey))
			continue
		}
		if queryInfo.JSFile == "" {
			e.logMessage(fmt.Sprintf("❌ No jsfile specified for query: %s", queryKey))
			continue
		}
		jsFileName := queryInfo.JSFile + ".js"
		jsFilePath := filepath.Join(e.config.JSPath, jsFileName)
		e.logMessage(fmt.Sprintf("🚀 Starting extraction for query '%s'", queryKey))
		data, err := e.extractTableData(dbPath, e.config.SQLiteTable, queryInfo.Query)
		if err != nil || len(data) == 0 {
			e.logMessage(fmt.Sprintf("⚠️ No data extracted for query: %s", queryKey))
			continue
		}
		e.logMessage(fmt.Sprintf("🔄 Processing data for '%s'...", queryKey))
		processed := e.processData(data)
		e.logMessage(fmt.Sprintf("💾 Saving to %s...", jsFileName))
		if err := e.saveToJS(processed, jsFilePath, queryKey); err != nil {
			continue
		}
	}
}

// extractTableData extracts data from SQLite database
func (e *SQLiteExtractor) extractTableData(dbPath, tableName, sqlQuery string) ([]Record, error) {
	if _, err := os.Stat(dbPath); os.IsNotExist(err) {
		e.logMessage(fmt.Sprintf("❌ Database not found: %s", dbPath))
		return nil, err
	}

	db, err := sql.Open("sqlite3", dbPath)
	if err != nil {
		e.logMessage(fmt.Sprintf("❌ Database error: %v", err))
		return nil, err
	}
	defer db.Close()

	// Check if table exists
	var name string
	err = db.QueryRow("SELECT name FROM sqlite_master WHERE type='table' AND name=?", tableName).Scan(&name)
	if err == sql.ErrNoRows {
		e.logMessage(fmt.Sprintf("❌ Table '%s' not found", tableName))
		return nil, err
	}
	if err != nil {
		e.logMessage(fmt.Sprintf("❌ Database error: %v", err))
		return nil, err
	}

	rows, err := db.Query(sqlQuery)
	if err != nil {
		e.logMessage(fmt.Sprintf("❌ Database error: %v", err))
		return nil, err
	}
	defer rows.Close()

	columns, err := rows.Columns()
	if err != nil {
		e.logMessage(fmt.Sprintf("❌ Database error: %v", err))
		return nil, err
	}

	var data []Record
	for rows.Next() {
		values := make([]interface{}, len(columns))
		valuePtrs := make([]interface{}, len(columns))
		for i := range values {
			valuePtrs[i] = &values[i]
		}
		if err := rows.Scan(valuePtrs...); err != nil {
			e.logMessage(fmt.Sprintf("❌ Database error: %v", err))
			return nil, err
		}
		record := make(Record)
		for i, col := range columns {
			record[col] = values[i]
		}
		data = append(data, record)
	}
	e.logMessage(fmt.Sprintf("✅ Extracted %d rows using query", len(data)))
	return data, nil
}

// processData processes data, sorting by timestamp if present
func (e *SQLiteExtractor) processData(data []Record) []Record {
	if len(data) == 0 {
		return data
	}

	// Identify timestamp columns
	var timestampCols []string
	for col := range data[0] {
		if strings.Contains(strings.ToLower(col), "timestamp") || strings.Contains(strings.ToLower(col), "date") {
			timestampCols = append(timestampCols, col)
		}
	}

	// Parse timestamps
	for _, record := range data {
		for _, col := range timestampCols {
			if val, ok := record[col].(string); ok {
				if parsed, err := time.Parse("2006-01-02 15:04:05", val); err == nil {
					record[col] = parsed
				}
			}
		}
	}

	// Sort by first timestamp column if present
	if len(timestampCols) > 0 {
		// Create a new slice to avoid modifying the original
		sortedData := make([]Record, len(data))
		copy(sortedData, data)

		// Sort in descending order
		for i := 0; i < len(sortedData)-1; i++ {
			for j := i + 1; j < len(sortedData); j++ {
				var t1, t2 time.Time
				if v1, ok := sortedData[i][timestampCols[0]].(time.Time); ok {
					t1 = v1
				}
				if v2, ok := sortedData[j][timestampCols[0]].(time.Time); ok {
					t2 = v2
				}
				if t2.After(t1) {
					sortedData[i], sortedData[j] = sortedData[j], sortedData[i]
				}
			}
		}
		e.logMessage(fmt.Sprintf("✅ Processed %d records", len(sortedData)))
		return sortedData
	}

	e.logMessage(fmt.Sprintf("✅ Processed %d records", len(data)))
	return data
}

// saveToJS saves data to a JavaScript file
func (e *SQLiteExtractor) saveToJS(data []Record, outputPath, queryKey string) error {
	outputDir := filepath.Dir(outputPath)
	if outputDir != "" {
		if err := os.MkdirAll(outputDir, 0755); err != nil {
			e.logMessage(fmt.Sprintf("❌ Write error: %v", err))
			return err
		}
	}

	jsContent := fmt.Sprintf(`// Auto-generated on %s
// Generated by SQLite Extractor Console
var Program = "%s";
var QueryName = "%s";
const DataIn = %s;

//if (typeof window !== 'undefined') {
//    window.DataIn = DataIn;
//}
`, time.Now().Format(time.RFC1123), e.config.WProgram, queryKey, marshalJSON(data))

	file, err := os.Create(outputPath)
	if err != nil {
		e.logMessage(fmt.Sprintf("❌ Write error: %v", err))
		return err
	}
	defer file.Close()

	if _, err := file.WriteString(jsContent); err != nil {
		e.logMessage(fmt.Sprintf("❌ Write error: %v", err))
		return err
	}

	e.logMessage(fmt.Sprintf("✅ Saved %s (%d records) - %s", filepath.Base(outputPath), len(data), time.Now().Format("15:04:05")))
	//e.logMessage("=============================1")
	e.logMessage("#############################")
	return nil
}

// marshalJSON converts data to JSON string with proper formatting
func marshalJSON(data []Record) string {
	jsonBytes, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return "[]"
	}
	return string(jsonBytes)
}

// startFileMonitoring starts monitoring the database file for changes
func (e *SQLiteExtractor) startFileMonitoring() error {
	if e.config.FilePath == "" || e.config.DBName == "" {
		e.logMessage("❌ Missing configuration: FILE_PATH or FILE_SQLITE")
		return fmt.Errorf("missing configuration")
	}

	dbPath := filepath.Join(e.config.FilePath, e.config.DBName+".db")
	dbDir := e.config.FilePath
	queryFile := filepath.Join(e.config.FilePath, "queries.json")

	if _, err := os.Stat(dbDir); os.IsNotExist(err) {
		e.logMessage(fmt.Sprintf("❌ Directory not found: %s", dbDir))
		return err
	}
	if _, err := os.Stat(dbPath); os.IsNotExist(err) {
		e.logMessage(fmt.Sprintf("❌ Database file not found: %s", dbPath))
		return err
	}

	var err error
	e.watcher, err = fsnotify.NewWatcher()
	if err != nil {
		e.logMessage(fmt.Sprintf("❌ Watcher error: %v", err))
		return err
	}

	go func() {
		for {
			select {
			case event, ok := <-e.watcher.Events:
				if !ok {
					return
				}
				if event.Name == dbPath && event.Op&fsnotify.Write == fsnotify.Write {
					currentModified := getFileModTime(dbPath)
					if e.lastDBModified != currentModified {
						e.lastDBModified = currentModified
						e.logMessage(fmt.Sprintf("📝 Detected change in %s.db", e.config.DBName))
						e.triggerExtraction()
					}
				}
				if event.Name == queryFile && event.Op&fsnotify.Write == fsnotify.Write {
					e.logMessage("📝 Query file updated")
				}
			case err, ok := <-e.watcher.Errors:
				if !ok {
					return
				}
				e.logMessage(fmt.Sprintf("❌ Watcher error: %v", err))
			}
		}
	}()

	if err := e.watcher.Add(dbDir); err != nil {
		e.logMessage(fmt.Sprintf("❌ Watcher error: %v", err))
		return err
	}
	if _, err := os.Stat(queryFile); !os.IsNotExist(err) {
		if err := e.watcher.Add(queryFile); err != nil {
			e.logMessage(fmt.Sprintf("❌ Watcher error: %v", err))
			return err
		}
	}

	e.logMessage("=============================")
	e.logMessage(fmt.Sprintf("🔍 Monitoring %s.db%s", e.config.DBName, func() string {
		if _, err := os.Stat(queryFile); !os.IsNotExist(err) {
			return " and queries.json"
		}
		return ""
	}()))
	e.logMessage("Press Ctrl+C to quit")
	e.startFallbackPolling(dbPath)
	return nil
}

// stopFileMonitoring stops monitoring the database file
func (e *SQLiteExtractor) stopFileMonitoring() {
	if e.watcher != nil {
		e.watcher.Close()
		e.watcher = nil
		e.logMessage("🛑 File monitoring stopped")
	}
	e.running = false
	e.isListening = false
	e.logMessage("🏁 Operation completed")
}

// startFallbackPolling starts polling for file changes
func (e *SQLiteExtractor) startFallbackPolling(dbPath string) {
	go func() {
		ticker := time.NewTicker(5 * time.Second)
		defer ticker.Stop()
		for e.isListening && e.running {
			select {
			case <-ticker.C:
				currentModified := getFileModTime(dbPath)
				if e.lastDBModified != currentModified {
					e.lastDBModified = currentModified
					e.logMessage(fmt.Sprintf("📝 Detected change in %s.db (polling)", e.config.DBName))
					e.triggerExtraction()
				}
			}
		}
	}()
	e.logMessage("=============================")
	e.logMessage("🔄 Started fallback polling")
	e.logMessage("Press Ctrl+C to quit")
}

// getFileModTime returns the modification time of a file as a float64
func getFileModTime(path string) float64 {
	info, err := os.Stat(path)
	if err != nil {
		return 0
	}
	return float64(info.ModTime().UnixNano()) / 1e9
}

// triggerExtraction triggers extraction when file changes
func (e *SQLiteExtractor) triggerExtraction() {
	if !e.isListening {
		e.isListening = true
	}
	e.logMessage("Processing SQLite Extraction...")
	e.extractAndSave()
	if e.isListening {
		e.logMessage(" ")
		e.logMessage("💾 FileWatcher by Nivra...")
		e.logMessage("✅ Extraction completed, continuing to monitor...")
		e.logMessage("Press Ctrl+C to quit")
	} else {
		e.logMessage("✅ Single extraction completed")
	}
	//e.logMessage("=============================4")
	e.logMessage("#############################")
}

// run handles the main console interaction loop
func (e *SQLiteExtractor) run() {
	if e.config.FilePath == "" || e.config.DBName == "" {
		e.logMessage("❌ Missing configuration: Please ensure FILE_PATH and FILE_SQLITE are set in .env")
		return
	}

	fmt.Printf("\nSQLite to JS Extractor - %s\n", e.config.WProgram)
	fmt.Println("1: Start continuous processing")
	fmt.Println("2: Perform single execution")
	fmt.Println("Press Ctrl+C to quit")

	for e.running {
		fmt.Print("\nEnter choice (1 or 2): ")
		var choice string
		_, err := fmt.Scanln(&choice)
		if err != nil {
			e.logMessage("❌ Invalid input, please enter 1 or 2")
			continue
		}

		switch choice {
		case "1":
			e.isListening = true
			if err := e.startFileMonitoring(); err != nil {
				return
			}
			for e.isListening && e.running {
				time.Sleep(1 * time.Second)
			}
		case "2":
			e.logMessage("🚀 Starting single execution...")
			e.triggerExtraction()
			e.isListening = false
			fmt.Printf("\nSQLite to JS Extractor - %s\n", e.config.WProgram)
			fmt.Println("1: Start continuous processing")
			fmt.Println("2: Perform single execution")
			fmt.Println("Press Ctrl+C to quit")
		default:
			e.logMessage("❌ Invalid choice. Please enter 1 or 2.")
		}
	}
}

func main() {
	extractor, err := NewSQLiteExtractor()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error initializing extractor: %v\n", err)
		os.Exit(1)
	}

	// Handle Ctrl+C
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)
	go func() {
		<-sigChan
		extractor.logMessage("🛑 Received Ctrl+C, exiting...")
		extractor.stopFileMonitoring()
		os.Exit(0)
	}()

	extractor.run()
}